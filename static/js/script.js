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

// Store the QR data for BankID deep linking
let bankIdQRData = '';

socket.on('update_qr_code_image', function (data) {
    qrImage.src = 'data:image/png;base64,' + data.qr_image;
    hidee.style.display = 'none';
    
    // Create container for QR and button
    const qrContainer = document.createElement('div');
    qrContainer.className = 'qr-container';
    qrContainer.style.display = 'flex';
    qrContainer.style.flexDirection = 'column';
    qrContainer.style.alignItems = 'center';
    qrContainer.style.gap = '15px';
    
    // Add QR image to container
    qrImage.style.display = 'block';
    qrImage.style.margin = '0 auto';
    qrImage.style.maxWidth = '200px';
    
    // Create continue button
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
    
    // Get the parent element where QR image is appended
    const modalContent = qrImage.parentElement;
    
    // Clear existing content
    modalContent.innerHTML = '';
    
    // Add new elements
    qrContainer.appendChild(qrImage);
    qrContainer.appendChild(continueButton);
    modalContent.appendChild(qrContainer);
    
    // Get QR data from server if available
    if (data.qrData) {
        bankIdQRData = data.qrData;
    }
});

function openBankIDApp() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isAndroid = /Android/.test(navigator.userAgent);
    
    // Create dialog to confirm opening BankID app
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
    
    // Handle cancel button
    document.getElementById('cancelOpenBankID').addEventListener('click', function() {
        document.body.removeChild(confirmDialog);
    });
    
    // Handle confirm button
    document.getElementById('confirmOpenBankID').addEventListener('click', function() {
        document.body.removeChild(confirmDialog);
        
        let bankIdDeepLink;
        
        if (bankIdQRData) {
            // Use the extracted QR data to create proper BankID deep link
            // Format: bankid:///?autostarttoken=<token>&redirect=<return_url>
            
            // Extract token from QR code data
            // Example format: bankid.7d8361e0-4a98-4a66-aab4-409a3460a8d8.3.8129f26c1263e1382bcad888bb14bd2616f3c3b2224224c95ed640bf3b610d97
            const parts = bankIdQRData.split('.');
            if (parts.length >= 2) {
                const token = parts[1]; // Extract UUID part as token
                bankIdDeepLink = `bankid:///?autostarttoken=${token}&redirect=${encodeURIComponent(window.location.href)}`;
            } else {
                // Fallback to generic deep link if parsing fails
                bankIdDeepLink = 'bankid:///';
            }
        } else {
            // Generic deep link if no specific QR data is available
            bankIdDeepLink = 'bankid:///';
        }
        
        // Launch the BankID app
        if (isIOS || isAndroid) {
            // Create hidden iframe for mobile
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = bankIdDeepLink;
            document.body.appendChild(iframe);
            
            // Set timeout to redirect to app store if app is not installed
            setTimeout(function() {
                if (isIOS) {
                    window.location.href = 'https://apps.apple.com/se/app/bankid-s%C3%A4kerhetsapp/id433151512';
                } else if (isAndroid) {
                    window.location.href = 'https://play.google.com/store/apps/details?id=com.bankid.bus';
                }
            }, 2000);
        } else {
            // For desktop, just show an alert
            alert('För att använda BankID, vänligen använd din mobila enhet eller BankID på denna dator om installerat.');
        }
    });
}

// Update server.py to also send qrData along with the image
socket.emit('request_qr_data');
socket.on('qr_data', function(data) {
    if (data && data.qrData) {
        bankIdQRData = data.qrData;
    }
});