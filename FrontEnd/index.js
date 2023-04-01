// Variables for accessing the API Gateway endpoints
const API_BASE_URL = 'https://i931perub3.execute-api.us-east-1.amazonaws.com/Prod';
const SEARCH_ENDPOINT = '/search';
const UPLOAD_ENDPOINT = '/upload/photo-storage-b2-cf/';

// Function to handle text search
function textSearch() {
  // Get the search query from the input field
  const searchQuery = document.getElementById('search_query').value;

  // Make an HTTP GET request to the search endpoint with the search query as a parameter
  fetch(API_BASE_URL + SEARCH_ENDPOINT + '?q=' + searchQuery)
    .then(response => response.json())
    .then(data => {
      console.log(data);
      if (data === 'No Results found') {
        var photosDiv = document.getElementById("photos_search_results");
        photosDiv.innerHTML = "";

        // Create a new HTML element to display the message
        const message = document.createElement('p');
        message.textContent = 'No photos found';
        photosDiv.appendChild(message);
    } else {
        var photosDiv = document.getElementById("photos_search_results");
        photosDiv.innerHTML = "";
        
        for (let i = 0; i < data.imagePaths.length; i++) {
            const photo_path = data.imagePaths[i];
        
            const photoHtml = '<figure style="display:inline-block; margin:10px; width:calc(100%/3 - 20px)">' +
                                '<img src="' + `${photo_path}` + '" style="width:100%">' +
                                '<figcaption style="text-align:center">' + photo_path.split('/')[3].split('?')[0] + '</figcaption>' +
                            '</figure>';
            photosDiv.innerHTML += photoHtml;
        }
      }
    })
    .catch(error => console.log(error));
}

// Function to perform a voice search
function voiceSearch() {
  const $micIcon = $('#mic_search');
  const recognition = new webkitSpeechRecognition();

  recognition.onstart = function() {
    $micIcon.text('mic_off');
  };

  recognition.onresult = function(event) {
    const query = event.results[0][0].transcript;
    $('#search_query').val(query);
    textSearch();
  };

  recognition.onerror = function(event) {
    console.error(event.error);
  };

  recognition.onend = function() {
    $micIcon.text('mic');
  };

  recognition.start();
}

// Function to handle photo upload
function uploadPhoto() {
  // Get the uploaded file and custom labels from the input fields
  const uploadedFile = document.getElementById('uploaded_file').files[0];
  const customLabels = document.getElementById('custom_labels').value;

  // Create a new FormData object and append the uploaded file and custom labels to it
  const formData = new FormData();
  formData.append('file', uploadedFile);
  formData.append('labels', customLabels);

  const fileInput = document.getElementById('uploaded_file');
  const fileName = fileInput.value.split('\\').pop(); 
  const fileType = fileName.split('.').pop();
  console.log(fileName); 
  console.log('file type',fileType);
  console.log('cusLab', customLabels);


  // Make an HTTP PUT request to the upload endpoint with the file and custom labels as parameters
  fetch(API_BASE_URL + UPLOAD_ENDPOINT + fileName, {
    method: 'PUT',
    headers: {
      "x-amz-meta-customLabels": customLabels,
      "Content-Type": `image/${fileType}`,
      "x-api-key": "EJj1AAyQwB6kTf5PN6N079TIoWzxGbeJ9nQutCVY"
    },
    body: uploadedFile
  })
    .then(response => response)
    .then(data => console.log(data))
    .catch(error => console.log(error));
}
