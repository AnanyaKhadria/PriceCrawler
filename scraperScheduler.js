const axios = require('axios');
const cron = require('node-cron');

const endpoints = [
    'http://localhost:5000/scrape/cashify',
    'http://localhost:5000/scrape/cashmen',
    'http://localhost:5000/scrape/quickmobile',
    'http://localhost:5000/scrape/instacash'
];

const triggerScrapers = async () => {
    console.log(`Triggering scrapers at ${new Date().toLocaleString()}`);
    
    try {
        const requests = endpoints.map(url =>
            axios.get(url)
                .then(response => ({ url, status: "success", data: response.data }))
                .catch(error => ({ url, status: "error", error: error.message }))
        );

        const results = await Promise.allSettled(requests);

        results.forEach(result => {
            if (result.status === "fulfilled") {
                console.log(`Success: ${result.value.url}`);
                console.log(result.value.data);
            } else {
                console.error(`Error: ${result.reason.url}`);
                console.error(result.reason.error);
            }
        });

    } catch (error) {
        console.error("Unexpected error:", error);
    }
};

// Run immediately, then every 3 hours
triggerScrapers();

// 3 hours in milliseconds
//setInterval(triggerScrapers, 3 * 60 * 60 * 1000);  


//Run after every 3 hours
cron.schedule('0 */3 * * *', () => {
    console.log("Scheduled job running...");
    triggerScrapers();
});
