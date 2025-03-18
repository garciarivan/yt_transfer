// Script para la aplicación de transferencia de suscripciones de YouTube

document.addEventListener('DOMContentLoaded', function() {
    // Mostrar modal de error de cuota si hay una alerta relacionada con la cuota
    const alertElements = document.querySelectorAll('.alert.alert-warning');
    alertElements.forEach(alert => {
        if (alert.textContent.toLowerCase().includes('límite diario') || 
            alert.textContent.toLowerCase().includes('cuota') || 
            alert.textContent.toLowerCase().includes('24 horas')) {
            
            // Ocultar la alerta original
            alert.style.display = 'none';
            
            // Mostrar modal de error de cuota
            const quotaErrorModal = new bootstrap.Modal(document.getElementById('quotaErrorModal'));
            quotaErrorModal.show();
        }
    });
    
    // Manejo de los formularios de transferencia y modales
    const transferForms = document.querySelectorAll('.transfer-form');
    
    transferForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const transferType = this.getAttribute('data-transfer-type') || 'contenido';
            
            // Solo mostrar la confirmación si no estamos en las páginas de selección
            // porque esas ya tienen su propia confirmación
            if (!this.id.includes('subscription-form') && 
                !this.id.includes('liked-videos-form') && 
                !this.id.includes('playlists-form')) {
                
                e.preventDefault();
                
                if (!confirm(`¿Estás seguro de que deseas transferir ${transferType}? Este proceso puede tardar varios minutos.`)) {
                    return false;
                }
                
                // Mostrar modal de carga
                const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
                document.getElementById('transferTypeText').innerText = `Transfiriendo ${transferType}...`;
                loadingModal.show();
                
                // Enviar el formulario
                setTimeout(() => {
                    this.submit();
                }, 500);
            }
        });
    });
    
    // Mostrar modal de resumen si hay datos de resumen
    if (document.getElementById('summaryModal') && 
        document.querySelector('#summaryModal .row .col-md-4')) {
        
        const summaryModal = new bootstrap.Modal(document.getElementById('summaryModal'));
        summaryModal.show();
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
    
    // Animación para los logos de cuenta
    const accountAvatars = document.querySelectorAll('.account-avatar');
    accountAvatars.forEach(avatar => {
        avatar.addEventListener('mouseenter', function() {
            const img = this.querySelector('img');
            if (img) {
                img.style.transform = 'scale(1.2) rotate(10deg)';
            }
        });
        
        avatar.addEventListener('mouseleave', function() {
            const img = this.querySelector('img');
            if (img) {
                img.style.transform = '';
            }
        });
    });
}); 