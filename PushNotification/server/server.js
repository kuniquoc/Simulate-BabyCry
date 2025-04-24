const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
const PORT = 3000;

// Middleware
app.use(bodyParser.json());
app.use(cors());

// Queue to process cry detection
let lastTimestamp = 0;
const notifications = [];

// Mutex to synchronize access to lastTimestamp
let isUpdatingTimestamp = false;

// API to add notifications
app.post('/api/notifications', async (req, res) => {
    const { timestamp, message } = req.body;

    if (!timestamp) {
        return res.status(400).json({ error: 'Invalid payload: timestamp is required' });
    }

    if (!isUpdatingTimestamp) {
        isUpdatingTimestamp = true;
        
        // Check if we're within the threshold time
        if (timestamp - lastTimestamp < 60) {
            isUpdatingTimestamp = false;
            return res.status(200).json({ message: 'Notification already sent' });
        }

        // Add notification directly
        lastTimestamp = timestamp;
        notifications.push(message || `Cry detected from ${new Date(timestamp * 1000).toLocaleString()}`);
        
        isUpdatingTimestamp = false;
    }

    res.status(200).json({ message: 'Notification added' });
});

// Add a GET endpoint for the client to fetch notifications
app.get('/api/notifications', (req, res) => {
    try {
        // Check if notifications are available
        if (notifications.length > 0) {
            // Return notifications and clear them after sending
            const response = [...notifications];
            notifications.length = 0; // Clear notifications after sending
            res.status(200).json(response);
        } else {
            res.status(200).json({ message: 'No new notifications' });
        }
    }
    catch (error) {
        console.error('Error fetching notifications:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});