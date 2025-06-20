// Global variables
let convertedMarkdown = '';
let eventSource = null;
let accumulatedMarkdown = '';

// Check for saved API key on load
window.onload = async function() {
    try {
        const response = await fetch('/check-api-key');
        const result = await response.json();
        if (result.hasKey) {
            showUploadSection();
            // Check for URL parameter after showing upload section
            checkForURLParameter();
        }
    } catch (error) {
        console.error('Error checking API key:', error);
    }
    
    // Set up drag and drop after DOM is loaded
    setupDragAndDrop();
};

async function saveApiKey() {
    const key = document.getElementById('api-key').value;
    if (!key) {
        alert('Please enter an API key');
        return;
    }
    
    try {
        const response = await fetch('/save-api-key', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({key: key})
        });
        
        const result = await response.json();
        if (result.success) {
            showUploadSection();
        }
    } catch (error) {
        showError('Failed to save API key: ' + error.message);
    }
}

function showUploadSection() {
    document.getElementById('api-key-section').style.display = 'none';
    document.getElementById('upload-section').style.display = 'flex';
}

async function resetApiKey() {
    if (confirm('Are you sure you want to reset your API key?')) {
        try {
            await fetch('/reset-api-key', {method: 'POST'});
            location.reload();
        } catch (error) {
            showError('Failed to reset API key: ' + error.message);
        }
    }
}

// Set up drag and drop functionality
function setupDragAndDrop() {
    const uploadArea = document.getElementById('upload-area');
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        handleFile(file);
    }
}

async function handleFile(file) {
    // Hide input elements when processing starts
    document.getElementById('upload-area').style.display = 'none';
    document.getElementById('url-input-container').style.display = 'none';
    
    // Reset UI
    document.getElementById('error-message').style.display = 'none';
    document.getElementById('output-container').style.display = 'none';
    document.getElementById('progress-container').style.display = 'block';
    document.getElementById('markdown-output').innerHTML = '';
    accumulatedMarkdown = '';
    convertedMarkdown = '';
    document.getElementById('progress-fill').style.width = '20%';
    document.getElementById('status-text').textContent = 'Uploading file...';
    
    try {
        const formData = new FormData();
        formData.append('file', file);

        // Upload file and process with streaming response
        const response = await fetch('/convert-stream', {
            method: 'POST',
            body: formData
        });

        document.getElementById('progress-fill').style.width = '50%';
        document.getElementById('status-text').textContent = 'Converting to markdown...';

        // Read the streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, {stream: true});
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.chunk) {
                            accumulatedMarkdown += data.chunk;
                            convertedMarkdown = accumulatedMarkdown;
                            
                            // Convert markdown to HTML and display
                            const html = marked.parse(accumulatedMarkdown);
                            document.getElementById('markdown-output').innerHTML = html;
                            
                            document.getElementById('output-container').style.display = 'block';
                            document.getElementById('status-text').textContent = 'Converting...';
                            
                            // Auto-scroll
                            const markdownDisplay = document.getElementById('markdown-output');
                            markdownDisplay.scrollTop = markdownDisplay.scrollHeight;
                        } else if (data.done) {
                            document.getElementById('progress-container').style.display = 'none';
                            convertedMarkdown = accumulatedMarkdown;
                        } else if (data.error) {
                            showError(data.error);
                            break;
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }

    } catch (error) {
        showError('Error processing file: ' + error.message);
    }
}

async function handleURL() {
    const urlInput = document.getElementById('url-input').value.trim();
    
    if (!urlInput) {
        showError('Please enter a URL');
        return;
    }

    // Basic URL validation
    try {
        new URL(urlInput);
    } catch (e) {
        showError('Please enter a valid URL');
        return;
    }

    // Hide input elements when processing starts
    document.getElementById('upload-area').style.display = 'none';
    document.getElementById('url-input-container').style.display = 'none';
    
    // Reset UI
    document.getElementById('error-message').style.display = 'none';
    document.getElementById('output-container').style.display = 'none';
    document.getElementById('progress-container').style.display = 'block';
    document.getElementById('markdown-output').innerHTML = '';
    accumulatedMarkdown = '';
    convertedMarkdown = '';
    document.getElementById('progress-fill').style.width = '20%';
    document.getElementById('status-text').textContent = 'Fetching URL...';
    
    // Close any existing EventSource
    if (eventSource) {
        eventSource.close();
    }

    try {
        // Send URL to backend with EventSource for streaming
        eventSource = new EventSource('/convert-url-stream?url=' + encodeURIComponent(urlInput));
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.chunk) {
                accumulatedMarkdown += data.chunk;
                convertedMarkdown = accumulatedMarkdown;
                
                // Convert markdown to HTML and display as rich text
                const html = marked.parse(accumulatedMarkdown);
                document.getElementById('markdown-output').innerHTML = html;
                
                document.getElementById('output-container').style.display = 'block';
                document.getElementById('progress-fill').style.width = '70%';
                document.getElementById('status-text').textContent = 'Converting...';
                
                // Auto-scroll
                const markdownDisplay = document.getElementById('markdown-output');
                markdownDisplay.scrollTop = markdownDisplay.scrollHeight;
            } else if (data.done) {
                document.getElementById('progress-container').style.display = 'none';
                convertedMarkdown = accumulatedMarkdown;
                eventSource.close();
            } else if (data.error) {
                showError(data.error);
                eventSource.close();
            }
        };

        eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            showError('Failed to process URL. Please check if the site is accessible.');
            eventSource.close();
        };

    } catch (error) {
        showError(error.message);
    }
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-message').style.display = 'block';
    document.getElementById('progress-container').style.display = 'none';
    // Show input elements again on error
    document.getElementById('upload-area').style.display = 'block';
    document.getElementById('url-input-container').style.display = 'block';
}

function downloadMarkdown() {
    const blob = new Blob([convertedMarkdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'converted-document.md';
    a.click();
    URL.revokeObjectURL(url);
}

function copyPlaintext() {
    const plaintext = document.getElementById('markdown-output').innerText;
    navigator.clipboard.writeText(plaintext).then(() => {
        showSuccessMessage('Plaintext copied to clipboard!');
    }).catch(err => {
        showError('Failed to copy: ' + err.message);
    });
}

function copyMarkdown() {
    navigator.clipboard.writeText(convertedMarkdown).then(() => {
        showSuccessMessage('Markdown copied to clipboard!');
    }).catch(err => {
        showError('Failed to copy: ' + err.message);
    });
}

async function copyRichText() {
    try {
        let html = document.getElementById('markdown-output').innerHTML;
        const plaintext = document.getElementById('markdown-output').innerText;
        
        // Convert HTML to be more Slack-compatible
        html = html.replace(/<strong>/g, '<b>').replace(/<\/strong>/g, '</b>');
        html = html.replace(/<p>/g, '<p style="margin: 0 0 1em 0;">').replace(/<\/p>/g, '</p>');
        html = html.replace(/(<h[1-6]>)/g, '<br>$1');
        html = html.replace(/<li>/g, '<li style="margin: 0.25em 0;">');
        html = html.replace(/<\/p>\s*<p/g, '</p><br><p');
        
        // Create a complete HTML document
        const fullHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.5; }
b { font-weight: bold; }
i, em { font-style: italic; }
p { margin: 0 0 1em 0; }
h1, h2, h3, h4, h5, h6 { font-weight: bold; margin: 0.5em 0; }
ul, ol { margin: 0.5em 0; padding-left: 1.5em; }
li { margin: 0.25em 0; }
code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-family: monospace; }
pre { background-color: #f4f4f4; padding: 8px; border-radius: 4px; overflow-x: auto; margin: 1em 0; }
blockquote { border-left: 4px solid #ddd; margin: 0.5em 0; padding-left: 1em; color: #666; }
</style>
</head>
<body>${html}</body>
</html>`;
        
        // Write both HTML and plain text for compatibility
        const htmlBlob = new Blob([fullHtml], { type: 'text/html' });
        const textBlob = new Blob([plaintext], { type: 'text/plain' });
        
        const clipboardItem = new ClipboardItem({
            'text/html': htmlBlob,
            'text/plain': textBlob
        });
        
        await navigator.clipboard.write([clipboardItem]);
        showSuccessMessage('Rich text copied to clipboard!');
    } catch (err) {
        // Fallback to plain text
        navigator.clipboard.writeText(document.getElementById('markdown-output').innerText).then(() => {
            showSuccessMessage('Copied as plain text (rich text not supported)');
        }).catch(err2 => {
            showError('Failed to copy: ' + err2.message);
        });
    }
}

function showSuccessMessage(message) {
    document.getElementById('success-message').textContent = message;
    document.getElementById('success-message').style.display = 'block';
    setTimeout(() => {
        document.getElementById('success-message').style.display = 'none';
        document.getElementById('success-message').textContent = 'Copied to clipboard!';
    }, 2000);
}

function resetUI() {
    // Show input elements again
    document.getElementById('upload-area').style.display = 'block';
    document.getElementById('url-input-container').style.display = 'block';
    
    // Hide output and reset values
    document.getElementById('output-container').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';
    document.getElementById('markdown-output').innerHTML = '';
    document.getElementById('url-input').value = '';
    document.getElementById('file-input').value = '';
    convertedMarkdown = '';
    accumulatedMarkdown = '';
    
    // Close any existing EventSource
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
}

function checkForURLParameter() {
    // Check query parameters for URL
    const searchParams = new URLSearchParams(window.location.search);
    const urlParam = searchParams.get('url');
    
    if (urlParam) {
        try {
            new URL(urlParam); // Validate URL
            document.getElementById('url-input').value = urlParam;
            
            // Automatically trigger conversion after a short delay
            setTimeout(() => {
                console.log('Auto-converting URL from query:', urlParam);
                handleURL();
            }, 500);
        } catch (e) {
            console.error('Invalid URL in query parameter:', urlParam);
        }
    }
}

function openReaderMode() {
    if (!convertedMarkdown) {
        showError('No content to display in reader mode');
        return;
    }
    
    // Create reader mode HTML
    const readerHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reader Mode</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"><\/script>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #fafafa;
            color: #333;
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.8;
            font-size: 18px;
        }
        .reader-container {
            max-width: 700px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #fff;
            min-height: 100vh;
            box-shadow: 0 0 20px rgba(0,0,0,0.05);
        }
        .close-button {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #666;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            z-index: 1000;
        }
        .close-button:hover {
            background: #555;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-weight: 600;
            margin: 1.5em 0 0.5em 0;
            line-height: 1.3;
        }
        h1 { font-size: 2.2em; }
        h2 { font-size: 1.8em; }
        h3 { font-size: 1.4em; }
        p {
            margin: 0 0 1.5em 0;
        }
        blockquote {
            margin: 1.5em 0;
            padding-left: 1em;
            border-left: 4px solid #ddd;
            color: #666;
            font-style: italic;
        }
        code {
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
        }
        pre {
            background-color: #f5f5f5;
            padding: 1em;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 0.9em;
            line-height: 1.5;
        }
        pre code {
            background: none;
            padding: 0;
        }
        ul, ol {
            margin: 1em 0;
            padding-left: 2em;
        }
        li {
            margin: 0.5em 0;
        }
        a {
            color: #2563eb;
            text-decoration: underline;
        }
        a:hover {
            color: #1d4ed8;
        }
        hr {
            border: none;
            border-top: 1px solid #e5e7eb;
            margin: 2em 0;
        }
        table {
            border-collapse: collapse;
            margin: 1.5em 0;
            width: 100%;
        }
        th, td {
            border: 1px solid #e5e7eb;
            padding: 8px 12px;
            text-align: left;
        }
        th {
            background-color: #f5f5f5;
            font-weight: 600;
        }
        @media (max-width: 768px) {
            body {
                font-size: 16px;
            }
            .reader-container {
                padding: 20px 15px;
            }
            .close-button {
                top: 10px;
                right: 10px;
            }
        }
    </style>
</head>
<body>
    <button class="close-button" onclick="window.close()">Close</button>
    <div class="reader-container" id="content"></div>
    <script>
        // Markdown content passed from parent window
        const markdown = ${JSON.stringify(convertedMarkdown)};
        
        // Convert to HTML and display
        document.getElementById('content').innerHTML = marked.parse(markdown);
        
        // Handle ESC key to close
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                window.close();
            }
        });
    <\/script>
</body>
</html>`;
    
    // Open reader mode window
    const readerWindow = window.open('', 'readerMode', 'width=800,height=900,menubar=no,toolbar=no,location=no,status=no');
    readerWindow.document.write(readerHTML);
    readerWindow.document.close();
}