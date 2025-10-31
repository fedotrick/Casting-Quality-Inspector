// Common JavaScript functions

// Close shift function
async function closeShift() {
    if (!confirm('Вы уверены, что хотите закрыть смену?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/close-shift', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        
        if (data.success) {
            alert('Смена успешно закрыта');
            window.location.href = '/';
        } else {
            alert('Ошибка при закрытии смены: ' + data.error);
        }
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Proceed to input function
function proceedToInput(cardNumber) {
    window.location.href = `/input-control?card=${cardNumber}`;
}

// Flash message auto-hide
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000);
    });
});
