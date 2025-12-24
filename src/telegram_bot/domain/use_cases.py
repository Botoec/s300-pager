from typing import Optional

import jwt
from datetime import datetime, timedelta
import structlog

from telegram_bot.config import settings
from telegram_bot.domain.entities import PhoneAuth, JwtTokens, CallEvent
# from ports import (
#     AuthPort,
#     MessagePort,
#     StoragePort,
# )
# from domain import (
#     PhoneAuth,
#     JwtTokens,
#     CallEvent,
# )


from telegram_bot.ports.auth_port import AuthPort
from telegram_bot.ports.redis_storage_port import RedisStoragePort
from telegram_bot.ports.message_port import MessagePort



logger = structlog.get_logger()


class PhoneAuthUseCase:
    def __init__(self, auth_port: AuthPort, redis_storage_port: RedisStoragePort):
        self.auth_port = auth_port
        self.redis_storage_port = redis_storage_port

    async def execute(self, phone_auth: PhoneAuth) -> dict:
        result = await self.auth_port.verify_phone(phone_auth.phone_number, phone_auth.user_id)
        if isinstance(result, dict) and result.get('code') == 'accounts_not_found':
            return {
                'message': 'Ваш номер телефона не найден. Пожалуйста, свяжитесь со '
                           'службой технической поддержки +78123857300 (добавочный 200) '
                           'и скажите, что у Вас не получается зарегистрироваться '
                           'в телеграм-боте «Пейджер.»'
            }

        elif isinstance(result, list):
            from collections import defaultdict
            org_employees = defaultdict(list)
            for employee in result:
                org_name = employee['provider']['str_name']
                org_employees[org_name].append(employee)

            organizations = []
            conflict_messages = []
            tokens = {}  # Хранение токенов по организациям или общий

            # TODO авторизация первого пользователя, на FE в ЛК проверить переключение
            #  (в client-panel-v4 создать задачу на переключение)
            for org_name, employees in org_employees.items():
                logger.warning(f'org_employees: {org_employees}')
                if len(employees) > 1:
                    conflict_messages.append(
                        f'В организации {org_name} Ваш номер телефона привязан к нескольким '
                        f'сотрудникам. Для получения уведомлений по этой организации необходимо '
                        f'настроить уникальный номер для каждого сотрудника. Пожалуйста, '
                        f'обратитесь к своему руководителю, чтобы решить эту проблему.'
                    )
                else:
                    employee = employees[0]
                    profile_number = employee['number']

                    try:
                        auth_result = await self.auth_port.authenticate(profile_number, phone_auth.user_id)  # Вызов authenticate
                        access_token = auth_result['access_token']
                        refresh_token = auth_result['refresh_token']
                        tokens[org_name] = {'access_token': access_token, 'refresh_token': refresh_token}
                        organizations.append(org_name)
                    except Exception as e:
                        logger.error(f"Auth error for {org_name}: {e}")
                        conflict_messages.append(f'Ошибка авторизации в {org_name}.')

            if conflict_messages:
                return {'message': '\n'.join(conflict_messages)}

            if organizations:
                await self.redis_storage_port.set(f'user:{phone_auth.user_id}:orgs', organizations) # TODO ttl
                await self.redis_storage_port.set(f'user:{phone_auth.user_id}:tokens', tokens) # TODO ttl
                # await self.storage_port.set(f'qr_token:{phone_auth.qr_token}')

                return {
                    'message': 'Вы успешно авторизованы. Теперь вы будете получать '
                               'уведомления по всем организациям, где вы состоите, прямо сюда.',
                    'status': 'success',
                }
            else:
                return {'message': 'Не найдено активных организаций для вашего номера.'}

        else:
            return {'message': 'Неизвестная ошибка авторизации.'}

class QrAuthUseCase:
    def __init__(self, auth_port: AuthPort, redis_storage_port: RedisStoragePort):
        self.auth_port = auth_port
        self.redis_storage_port = redis_storage_port

    async def validate_token(
            self,
            token_value: str,
            user_id: int
    ) -> bool | dict:
        token_data = await self.redis_storage_port.get(f'qr_token:{token_value}')

        logger.warning(f'search token_data by qr_token:{token_value}')
        logger.warning(f'token_data: {token_data}')


        if not token_data:
            logger.warning(f'QR token не найден или просрочен')
            # TODO вывод в сообщение
            return False

        if token_data.get('status') in ('confirmed', 'used', 'cancelled'):
            logger.warning(f'QR token уже использован или отменен')
            return False


        # TODO отдельная валидация telegram_user_id

        return token_data

    async def confirm_auth(self, token_value: str, user_id: int) -> dict | bool:
        token_data = await self.validate_token(token_value, user_id)

        if not token_data:
            return False

        await self.update_token_status(token_value, token_data, user_id, 'confirmed')
        return token_data

    async def update_token_status(self, token_value: str, token_data: dict, user_id: int, status: str) -> None:
        # TODO
        await self.redis_storage_port.set(
            f'qr_token:{token_value}',
            {
                **token_data,
                'telegram_user_id': user_id,
                'status': status,
            }
        )

    # async def _check_recheck_needed(self, user_id: int) -> bool:
    #     count = await self.redis_storage_port.incr(f'user:{user_id}:auth_count')
    #     last_check = await self.redis_storage_port.get(f'user:{user_id}:last_phone_check')
    #     if count % settings.PHONE_RECHECK_COUNT == 0 or (last_check and (datetime.now() - last_check) > timedelta(days=settings.PHONE_RECHECK_INTERVAL)):
    #         return True
    #     return False

class NotificationUseCase:
    def __init__(self, message_port: MessagePort, redis_storage_port: RedisStoragePort, auth_port: AuthPort):
        self.message_port = message_port
        self.redis_storage_port = redis_storage_port
        self.auth_port = auth_port

    async def handle_call_event(self, event: CallEvent):
        user_check = await self.auth_port.check_user_for_notifications(event)
        if not user_check['authorized'] or user_check['dnd'] == 'on' or not user_check['extension']:
            return

        if event.event_type == 'dial':
            msg_id = await self.message_port.send_message(event.user_id, self._format_incoming(event))
            await self.redis_storage_port.set(f'call:{event.call_id}:msg_id', msg_id)
        elif event.event_type in ['answer_call', 'end_call']:
            msg_id = await self.redis_storage_port.get(f'call:{event.call_id}:msg_id')
            if msg_id:
                await self.message_port.delete_message(event.user_id, msg_id)
        elif event.event_type == 'finish_call' and event.status == 'NO_ANSWER':
            msg_id = await self.message_port.send_message(
                event.user_id,
                self._format_missed(event),
                with_delete_button=True,
            )
            await self.redis_storage_port.set(f'missed_call:{event.call_id}:msg_id', msg_id)
        # Логика групповых: Если group_call, broadcast к нескольким user_id (симулируем)

    def _format_incoming(self, event: CallEvent) -> str:
        if event.caller_type == 'employee':
            return f"Вам звонят\n{event.caller_name}\n{event.phone}\n{event.organization}"
        return f"Вам звонят\n{event.caller_name}\n{event.phone}\n{event.address}"

    def _format_missed(self, event: CallEvent) -> str:
        if event.caller_type == 'employee':
            return f"Вам звонили\n{event.caller_name}\n{event.phone}\n{event.organization}"
        return f"Вам звонили\n{event.caller_name}\n{event.phone}\n{event.address}"
