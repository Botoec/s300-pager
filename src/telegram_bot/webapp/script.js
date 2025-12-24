const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const statusDiv = document.getElementById('status');
statusDiv.textContent = 'Инициализация...';

console.log("WebApp initData:", tg.initDataUnsafe);
console.log("WebApp version:", tg.version);
console.log("Platform:", tg.platform);

// Попап сканера
tg.showScanQrPopup({ text: "Наведите камеру на QR-код со страницы входа" }, (qrText) => {
    console.log("QR отсканирован:", qrText);

    if (qrText) {
        statusDiv.textContent = 'QR распознан: ' + qrText.substring(0, 20) + '...';
        statusDiv.textContent += '\nОтправка данных боту...';

        const url = new URL(qrText);
        const authToken = url.searchParams.get('start');

        if (!authToken) {
          throw new Error('Auth token not found in QR URL');
        }

        tg.sendData(authToken);

        setTimeout(() => {
            tg.close();
        }, 1000);
    } else {
        statusDiv.textContent = 'Сканирование отменено';
    }
    return true;
});
