// We only need to modify the relevant parts of the script.js file
// Here are the key sections that need fixing:

// Update the openBankIDApp function to correctly handle deep links
function openBankIDApp() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isAndroid = /Android/.test(navigator.userAgent);
    const isMobile = isIOS || isAndroid;
    
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
    confirmDialog.setAttribute('role', 'dialog');
    confirmDialog.setAttribute('aria-labelledby', 'dialogTitle');
    
    confirmDialog.innerHTML = `
        <h3 id="dialogTitle" style="margin-top: 0; color: #007aff;">Öppna BankID-appen</h3>
        <p>Vill du öppna BankID-appen för att fortsätta?</p>
        <div style="display: flex; justify-content: center; gap: 10px; margin-top: 20px;">
            <button id="cancelOpenBankID" style="padding: 8px 16px; background-color: #f1f1f1; border: none; border-radius: 4px; cursor: pointer;">Avbryt</button>
            <button id="confirmOpenBankID" style="padding: 8px 16px; background-color: #007aff; color: white; border: none; border-radius: 4px; cursor: pointer;">Öppna</button>
        </div>
    `;
    
    document.body.appendChild(confirmDialog);
    
    // Focus the confirm button for keyboard users
    setTimeout(() => {
        document.getElementById('confirmOpenBankID').focus();
    }, 100);
    
    // Allow closing with ESC key for better accessibility
    confirmDialog.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.body.removeChild(confirmDialog);
        }
    });
    
    // Handle cancel button
    document.getElementById('cancelOpenBankID').addEventListener('click', function() {
        document.body.removeChild(confirmDialog);
    });
    
    // Handle confirm button
    document.getElementById('confirmOpenBankID').addEventListener('click', function() {
        document.body.removeChild(confirmDialog);
        
        // Get the most recent QR code data
        socket.emit('request_fresh_qr_data');
        
        // Log current token data for debugging
        console.log("[BankID Debug] Current token data:", bankIdData);
        
        if (bankIdData.qrStartToken) {
            logDebug("Opening BankID app with token:", bankIdData.qrStartToken);
            
            // Create current URL to use as return URL
            const currentUrl = window.location.href;
            // Add a nonce to handle session matching
            const nonce = Date.now().toString(36) + Math.random().toString(36).substring(2);
            // Store nonce in sessionStorage for validation when returning
            sessionStorage.setItem('bankid_nonce', nonce);
            
            // Create return URL with nonce in fragment
            const baseReturnUrl = currentUrl.split('#')[0];
            const returnUrl = encodeURIComponent(`${baseReturnUrl}#nonce=${nonce}`);
            
            let bankidUrl = '';
            
            // Handle different URL formats based on platform
            if (isMobile) {
                // For mobile devices (iOS and Android), use universal/app links
                bankidUrl = `https://app.bankid.com/?autostarttoken=${bankIdData.qrStartToken}&redirect=${returnUrl}`;
                logDebug("Using mobile universal/app link:", bankidUrl);
            } else {
                // For desktop, use bankid:// protocol with redirect parameter
                bankidUrl = `bankid:///?autostarttoken=${bankIdData.qrStartToken}&redirect=${returnUrl}`;
                logDebug("Using desktop protocol:", bankidUrl);
            }
            
            // Open the BankID app - append timestamp to avoid browser caching
            window.location.href = bankidUrl + "&t=" + Date.now();
            
            // As a fallback, after a delay, show a message and offer to install the app
            setTimeout(function() {
                // Check if we're still on the same page (user hasn't been redirected)
                // Only show the fallback if there was no hash change indicating a return
                if (!window.location.hash.includes('nonce=')) {
                    showBankIDFallbackDialog(isIOS, isAndroid);
                }
            }, 3000);
        } else {
            // If we don't have a token, show an error message
            showErrorDialog("Ingen BankID-data tillgänglig. Var god skanna QR-koden igen.");
        }
    });
}

// Helper function to show fallback dialog
function showBankIDFallbackDialog(isIOS, isAndroid) {
    const dialogElement = document.createElement('div');
    dialogElement.className = 'bankid-fallback-dialog';
    dialogElement.style.position = 'fixed';
    dialogElement.style.top = '50%';
    dialogElement.style.left = '50%';
    dialogElement.style.transform = 'translate(-50%, -50%)';
    dialogElement.style.backgroundColor = 'white';
    dialogElement.style.padding = '20px';
    dialogElement.style.borderRadius = '8px';
    dialogElement.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    dialogElement.style.zIndex = '1000';
    dialogElement.style.maxWidth = '80%';
    dialogElement.style.textAlign = 'center';
    dialogElement.setAttribute('role', 'dialog');
    dialogElement.setAttribute('aria-labelledby', 'fallbackTitle');
    
    dialogElement.innerHTML = `
        <h3 id="fallbackTitle" style="margin-top: 0; color: #007aff;">BankID-appen kunde inte öppnas</h3>
        <p>BankID-appen verkar inte vara installerad eller kunde inte öppnas korrekt.</p>
        <div style="display: flex; justify-content: center; gap: 10px; margin-top: 20px;">
            <button id="dismissFallback" style="padding: 8px 16px; background-color: #f1f1f1; border: none; border-radius: 4px; cursor: pointer;">Avbryt</button>
            <button id="installBankID" style="padding: 8px 16px; background-color: #007aff; color: white; border: none; border-radius: 4px; cursor: pointer;">Installera BankID</button>
        </div>
    `;
    
    document.body.appendChild(dialogElement);
    
    // Focus the install button for keyboard users
    setTimeout(() => {
        document.getElementById('installBankID').focus();
    }, 100);
    
    // Dismiss button handler
    document.getElementById('dismissFallback').addEventListener('click', function() {
        document.body.removeChild(dialogElement);
    });
    
    // Install button handler
    document.getElementById('installBankID').addEventListener('click', function() {
        if (isIOS) {
            window.location.href = 'https://apps.apple.com/se/app/bankid-s%C3%A4kerhetsapp/id433151512';
        } else if (isAndroid) {
            window.location.href = 'https://play.google.com/store/apps/details?id=com.bankid.bus';
        } else {
            window.location.href = 'https://install.bankid.com/';
        }
        document.body.removeChild(dialogElement);
    });
    
    // Allow closing with ESC key
    dialogElement.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.body.removeChild(dialogElement);
        }
    });
}

// Helper function to show error dialog
function showErrorDialog(message) {
    const errorDialog = document.createElement('div');
    errorDialog.style.position = 'fixed';
    errorDialog.style.top = '50%';
    errorDialog.style.left = '50%';
    errorDialog.style.transform = 'translate(-50%, -50%)';
    errorDialog.style.backgroundColor = 'white';
    errorDialog.style.padding = '20px';
    errorDialog.style.borderRadius = '8px';
    errorDialog.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    errorDialog.style.zIndex = '1000';
    errorDialog.style.maxWidth = '80%';
    errorDialog.style.textAlign = 'center';
    
    errorDialog.innerHTML = `
        <h3 style="margin-top: 0; color: #ff3b30;">Fel</h3>
        <p>${message}</p>
        <button id="closeErrorDialog" style="padding: 8px 16px; background-color: #007aff; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 15px;">Stäng</button>
    `;
    
    document.body.appendChild(errorDialog);
    
    document.getElementById('closeErrorDialog').addEventListener('click', function() {
        document.body.removeChild(errorDialog);
    });
}

// Update the socket.on handler for qr_data
socket.on('qr_data', function(data) {
    logDebug("Received QR data:", data);
    
    if (data && data.qrData) {
        bankIdData.rawQrData = data.qrData;
        logDebug("Raw QR data:", bankIdData.rawQrData);
        
        // Parse the QR data for BankID format (bankid.token.time.authcode)
        const parts = data.qrData.split('.');
        if (parts.length >= 4 && parts[0] === 'bankid') {
            bankIdData.qrStartToken = parts[1];
            logDebug("Extracted qrStartToken from qrData:", bankIdData.qrStartToken);
        }
    }
    
    // Store token if available directly
    if (data && data.token) {
        bankIdData.qrStartToken = data.token;
        logDebug("Received token from qr_data:", bankIdData.qrStartToken);
    }
    
    // Store session ID if available
    if (data && data.session_id) {
        bankIdData.sessionId = data.session_id;
        logDebug("Received session ID from qr_data:", bankIdData.sessionId);
    }
    
    // Update lastUpdateTime when we receive QR data
    lastUpdateTime = Date.now();
});