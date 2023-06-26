function ip_characters_filter (event) {
    // Get the input value
    let inputValue = event.target.value;
    
    // Remove any characters that are not numbers, spaces, commas, or dots
    let filteredInputValue = inputValue.replace(/[^0-9,. ]+/g, '');
    // replace two or more spaces with 1 
    filteredInputValue = filteredInputValue.replace(/\s\s+/g, ' ');
    
    // If the input value was changed, update the input field value
    if (inputValue !== filteredInputValue) {
        event.target.value = filteredInputValue;
    }
}

const urlWhitelistInput = document.getElementById("url_whitelist");
const urlBlacklistInput = document.getElementById("url_blacklist");
const ipWhitelistInput = document.getElementById("ip_whitelist");
const ipBlacklistInput = document.getElementById("ip_blacklist");

ipBlacklistInput.addEventListener("input", ip_characters_filter);
ipWhitelistInput.addEventListener("input", ip_characters_filter);

const cacheTimeSlider = document.getElementById("cache_time");
const sliderOutput = document.getElementById("slider_output");

sliderOutput.innerHTML = cacheTimeSlider.value;

cacheTimeSlider.oninput = function() {
    sliderOutput.innerHTML = this.value;
}