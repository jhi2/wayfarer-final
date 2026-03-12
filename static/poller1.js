// Flask endpoint to poll
const endpoint = "{{ url_for('q_endpoint') }}";  // server-side generates the full URL

// Poll the endpoint repeatedly
function pollQueue() {
    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            console.log("Received:", data);

            // Detect nested list (positive response type)
            if (Array.isArray(data) && data.length > 0 && Array.isArray(data[0])) {
                console.log("Positive response detected!");

                // Use Flask url_for to build redirect URL, embedding JSON string
                const jsonStr = encodeURIComponent(JSON.stringify(data));
                const redirectUrl = "{{ url_for('pickssuc1') }}" + "?jsonstr=" + jsonStr;

                window.location.href = redirectUrl;
                return; // stop polling
            }

            // Optional: handle other statuses/errors
            if (data.error) console.warn("Error:", data.error);
            if (data.status) console.log("Status:", data.status);

            // Poll again after 2 seconds
            setTimeout(pollQueue, 2000);
        })
        .catch(err => {
            console.error("Fetch error:", err);
            setTimeout(pollQueue, 5000); // retry after 5s on error
        });
}

// Start polling
pollQueue();