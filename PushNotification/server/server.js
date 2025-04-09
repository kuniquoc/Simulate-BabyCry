const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
const PORT = 3000;

// Middleware
app.use(bodyParser.json());
app.use(cors());

// Queue to process cry detection
let cryQueue = [];
let lastTimestamp = 0;
const notifications = [];

// Mutex to synchronize access to lastTimestamp
let isUpdatingTimestamp = false;

// API to add notifications
app.post('/api/notifications', async (req, res) => {
    const { timestamp, probability } = req.body;

    if (!timestamp || typeof probability !== 'number') {
        return res.status(400).json({ error: 'Invalid payload' });
    }

    console.log(cryQueue);

    if (!isUpdatingTimestamp) {
        isUpdatingTimestamp = true;
        if (timestamp - lastTimestamp < 60) {

            isUpdatingTimestamp = false;
            return res.status(200).json({ message: 'Notification already sent' });
        }

        // Add to queue in sorted order
        const index = cryQueue.findIndex(item => item.timestamp > timestamp);
        if (index === -1) {
            cryQueue.push({ timestamp, probability });
        } else {
            cryQueue.splice(index, 0, { timestamp, probability });
        }

        // Maintain a buffer of the last 10 timestamps
        if (cryQueue.length > 10) {
            cryQueue.shift();
        }

        // Check for consecutive cry detections with at least 1 second difference
        if (cryQueue.length >= 2) {
            for (let i = 0; i < cryQueue.length - 1; i++) {
                const first = cryQueue[i];
                const second = cryQueue[i + 1];

                const timeDifference = (second.timestamp - first.timestamp); // Convert seconds to milliseconds

                if (timeDifference >= 1 && first.probability > 0.8 && second.probability > 0.8) {
                    lastTimestamp = first.timestamp; // Update last timestamp
                    notifications.push(`Cry detected from ${new Date(first.timestamp * 1000).toLocaleString()}`);
                    // Delete while 60 seconds from the last timestamp
                    const thresholdTime = lastTimestamp + 60;
                    cryQueue = cryQueue.filter(item => item.timestamp > thresholdTime);
                    break; // Exit loop after adding notification

                }
            }
        }

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