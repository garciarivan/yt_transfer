// Script para la aplicación de transferencia de suscripciones de YouTube

document.addEventListener('DOMContentLoaded', function() {
    // Ya no ocultamos las alertas automáticamente, ahora usan el botón de cierre
    
    // Añadir confirmación antes de iniciar la transferencia completa
    const transferForm = document.querySelector('form[action*="transfer"]');
    if (transferForm) {
        transferForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (confirm('¿Estás seguro de que deseas iniciar la transferencia de todas las suscripciones? Este proceso puede tardar varios minutos dependiendo del número de suscripciones.')) {
                this.submit();
            }
        });
    }
    
    // Animación para las tarjetas de autenticación
    const authCards = document.querySelectorAll('.auth-card');
    authCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 8px 15px rgba(0, 0, 0, 0.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
    });
    
    // Confirmación específica para cada tipo de transferencia
    const transferAllForm = document.getElementById('transfer-all-form');
    if (transferAllForm) {
        transferAllForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (confirm('¿Estás seguro de que deseas transferir TODO el contenido (suscripciones, videos con Me gusta y listas de reproducción)? Este proceso puede tardar varios minutos.')) {
                this.submit();
            }
        });
    }
    
    // Manejar formularios de transferencia individuales
    const transferForms = document.querySelectorAll('form[action*="transfer"]');
    transferForms.forEach(form => {
        if (form.id !== 'transfer-all-form' && form.querySelector('input[name="transfer_type"]')) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const transferType = this.querySelector('input[name="transfer_type"]').value;
                let confirmMessage = '';
                
                switch (transferType) {
                    case 'subscriptions':
                        confirmMessage = '¿Estás seguro de que deseas transferir todas tus suscripciones? Este proceso puede tardar varios minutos.';
                        break;
                    case 'liked_videos':
                        confirmMessage = '¿Estás seguro de que deseas transferir todos tus videos con Me gusta? Este proceso puede tardar varios minutos.';
                        break;
                    case 'playlists':
                        confirmMessage = '¿Estás seguro de que deseas transferir todas tus listas de reproducción? Este proceso puede tardar varios minutos.';
                        break;
                    default:
                        confirmMessage = '¿Estás seguro de que deseas iniciar esta transferencia? Este proceso puede tardar varios minutos.';
                }
                
                if (confirm(confirmMessage)) {
                    this.submit();
                }
            });
        }
    });
    
    // Efectos visuales para el menú de opciones
    const menuOptions = document.querySelectorAll('.menu-option');
    menuOptions.forEach(option => {
        option.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.1)';
            
            // Hacer que el icono gire suavemente
            const icon = this.querySelector('.option-icon i');
            if (icon) {
                icon.style.transition = 'transform 0.5s ease';
                icon.style.transform = 'rotate(10deg)';
            }
        });
        
        option.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
            
            // Restaurar el icono
            const icon = this.querySelector('.option-icon i');
            if (icon) {
                icon.style.transform = 'rotate(0deg)';
            }
        });
    });
}); 