document.addEventListener('DOMContentLoaded', () => {
    const notificationsDiv = document.getElementById('notifications');

    // Function to display a notification
    function displayNotification(notifications) {
        // Keep track of existing notifications
        const existingNotifications = Array.from(notificationsDiv.children).map(child => child.textContent);

        notifications.forEach(notification => {
            // Check if the notification already exists
            if (!existingNotifications.includes(notification)) {
                const notificationElement = document.createElement('div');
                notificationElement.className = 'notification';
                notificationElement.textContent = notification;
                notificationsDiv.appendChild(notificationElement);
            }
        });
    }

    // Simulate receiving a notification from the server
    setInterval(() => {
        fetch('http://localhost:3000/api/notifications')
            .then(response => response.json())
            .then(data => {
                if (data.message !== 'No new notifications') {
                    // Display the notification if it's not empty
                    displayNotification(data);
                }
            })
            .catch(err => console.error('Error fetching notifications:', err));
    }, 3000);
});