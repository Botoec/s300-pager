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
from telegram_bot.ports.storage_port import StoragePort
from telegram_bot.ports.message_port import MessagePort



logger = structlog.get_logger()


class PhoneAuthUseCase:
    def __init__(self, auth_port: AuthPort, storage_port: StoragePort):
        self.auth_port = auth_port
        self.storage_port = storage_port

    async def execute(self, phone_auth: PhoneAuth) -> dict:
        result = await self.auth_port.verify_phone(phone_auth.phone_number, phone_auth.user_id)
        if isinstance(result, dict) and result.get('code') == 'accounts_not_found':
            return {'message': 'Ваш номер телефона не найден. Пожалуйста, свяжитесь со службой технической поддержки +78123857300 (добавочный 200) и скажите, что у Вас не получается зарегистрироваться в телеграм-боте «Пейджер.»'}

        elif isinstance(result, list):
            from collections import defaultdict
            org_employees = defaultdict(list)
            for employee in result:
                org_name = employee['provider']['str_name']
                org_employees[org_name].append(employee)

            organizations = []
            conflict_messages = []
            tokens = {}  # Хранение токенов по организациям или общий

            # TODO авторизация первого пользователя, на FE в ЛК проверить переключение (в disp создать задачу на переключение)
            for org_name, employees in org_employees.items():
                logger.warning(f'org_employees: {org_employees}')
                if len(employees) > 1:
                    conflict_messages.append(
                        f'В организации {org_name} Ваш номер телефона привязан к нескольким сотрудникам. Для получения уведомлений по этой организации необходимо настроить уникальный номер для каждого сотрудника. Пожалуйста, обратитесь к своему руководителю, чтобы решить эту проблему.')
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
                # Сохраняем токены и организации в storage (Redis)
                await self.storage_port.set(f'user:{phone_auth.user_id}:orgs', organizations)
                await self.storage_port.set(f'user:{phone_auth.user_id}:tokens', tokens)  # С TTL для refresh_token lifetime

                return {
                    'message': 'Вы успешно авторизованы. Теперь вы будете получать уведомления по всем организациям, где вы состоите, прямо сюда.',
                    'status': 'success',
                }
            else:
                return {'message': 'Не найдено активных организаций для вашего номера.'}

        else:
            return {'message': 'Неизвестная ошибка авторизации.'}

class QrAuthUseCase:
    def __init__(self, auth_port: AuthPort, storage_port: StoragePort):
        self.auth_port = auth_port
        self.storage_port = storage_port

    async def validate_token(self, token_value: str, user_id: int) -> bool:
        token = await self.storage_port.get(f'auth_token:{token_value}')
        if not token or token['user_id'] != user_id or datetime.now() > token['expires_at']:
            return False
        # Проверка перепроверки номера (пример: счетчик в storage)
        recheck_needed = await self._check_recheck_needed(user_id)
        if recheck_needed:
            # Запрос перепроверки (симулируем)
            pass
        return True

    async def confirm_auth(self, token_value: str, user_id: int) -> JwtTokens:
        if await self.validate_token(token_value, user_id):
            # Генерация JWT (симуляция)
            access = jwt.encode({'user_id': user_id, 'exp': datetime.utcnow() + settings.ACCESS_TOKEN_LIFETIME}, 'secret')
            refresh = jwt.encode({'user_id': user_id, 'exp': datetime.utcnow() + settings.REFRESH_TOKEN_LIFETIME}, 'secret')
            await self.storage_port.delete(f'auth_token:{token_value}')  # Аннулировать
            return JwtTokens(access, refresh)
        return None

    async def _check_recheck_needed(self, user_id: int) -> bool:
        count = await self.storage_port.incr(f'user:{user_id}:auth_count')
        last_check = await self.storage_port.get(f'user:{user_id}:last_phone_check')
        if count % settings.PHONE_RECHECK_COUNT == 0 or (last_check and (datetime.now() - last_check) > timedelta(days=settings.PHONE_RECHECK_INTERVAL)):
            return True
        return False

class NotificationUseCase:
    def __init__(self, message_port: MessagePort, storage_port: StoragePort, auth_port: AuthPort):
        self.message_port = message_port
        self.storage_port = storage_port
        self.auth_port = auth_port

    async def handle_call_event(self, event: CallEvent):
        # Проверка предусловий (HTTP)
        user_check = await self.auth_port.check_user_for_notifications(event)
        if not user_check['authorized'] or user_check['dnd'] == 'on' or not user_check['extension']:
            return

        if event.event_type == 'dial':
            msg_id = await self.message_port.send_message(event.user_id, self._format_incoming(event))
            await self.storage_port.set(f'call:{event.call_id}:msg_id', msg_id)
        elif event.event_type in ['answer_call', 'end_call']:
            msg_id = await self.storage_port.get(f'call:{event.call_id}:msg_id')
            if msg_id:
                await self.message_port.delete_message(event.user_id, msg_id)
        elif event.event_type == 'finish_call' and event.status == 'NO_ANSWER':
            msg_id = await self.message_port.send_message(event.user_id, self._format_missed(event), with_delete_button=True)
            await self.storage_port.set(f'missed_call:{event.call_id}:msg_id', msg_id)
        # Логика групповых: Если group_call, broadcast к нескольким user_id (симулируем)

    def _format_incoming(self, event: CallEvent) -> str:
        if event.caller_type == 'employee':
            return f"Вам звонят\n{event.caller_name}\n{event.phone}\n{event.organization}"
        return f"Вам звонят\n{event.caller_name}\n{event.phone}\n{event.address}"

    def _format_missed(self, event: CallEvent) -> str:
        if event.caller_type == 'employee':
            return f"Вам звонили\n{event.caller_name}\n{event.phone}\n{event.organization}"
        return f"Вам звонили\n{event.caller_name}\n{event.phone}\n{event.address}"