async function checkConnectionStatus() {
  try {
    // Send a GET request to a known website (e.g., Google)
    const response = await fetch('https://www.google.com', { method: 'HEAD' });

    // Check if the response status is in the 200-299 range (success)
    if (response.status >= 200 && response.status <= 299) {
      console.log('Device is online.');
    } else {
      console.log('Device is offline.');
      await checkConnectionStatus();
    }
  } catch (error) {
    console.log('Device is offline.');
  }
}

checkConnectionStatus().then(r => console.log(r));
