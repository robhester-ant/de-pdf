// Global variables
let convertedMarkdown = '';
let eventSource = null;
let accumulatedMarkdown = '';

// Global variable to store URL parameter if present
let pendingUrlConversion = null;

// Check for saved API key on load
window.onload = async function() {
    // First, check if we have a URL parameter
    const searchParams = new URLSearchParams(window.location.search);
    const urlParam = searchParams.get('url');
    
    if (urlParam) {
        // Validate URL
        try {
            new URL(urlParam);
            // Store for later use
            pendingUrlConversion = urlParam;
        } catch (e) {
            console.error('Invalid URL in query parameter:', urlParam);
            // Hide loading and show error
            document.getElementById('initial-loading').style.display = 'none';
            document.getElementById('main-container').style.display = 'block';
            // Will show error after main UI loads
            setTimeout(() => showError('Invalid URL provided in query parameter'), 100);
            return;
        }
        
        // Initial loading is already shown by inline script
        // Update the loading message
        const statusText = document.querySelector('#initial-loading .status-text');
        if (statusText) {
            statusText.textContent = 'Checking API key...';
        }
    }
    
    try {
        const response = await fetch('/check-api-key');
        const result = await response.json();
        
        if (result.hasKey) {
            if (pendingUrlConversion) {
                // We have both API key and URL - start conversion immediately
                // Hide initial loading and show main container
                document.getElementById('initial-loading').style.display = 'none';
                document.getElementById('main-container').style.display = 'block';
                
                // Show upload section briefly to set up DOM
                showUploadSection();
                
                // Immediately start URL conversion
                document.getElementById('url-input').value = pendingUrlConversion;
                
                // Hide upload UI and show progress
                document.getElementById('upload-area').style.display = 'none';
                document.getElementById('url-input-container').style.display = 'none';
                document.getElementById('progress-container').style.display = 'block';
                document.getElementById('progress-fill').style.width = '30%';
                document.getElementById('status-text').textContent = 'Fetching URL...';
                
                // Start conversion without delay
                handleURL();
            } else {
                // No URL parameter, show normal upload interface
                showUploadSection();
            }
        } else {
            // No API key
            if (pendingUrlConversion) {
                // Show API key input but indicate we'll process URL after
                document.getElementById('initial-loading').style.display = 'none';
                document.getElementById('main-container').style.display = 'block';
                
                // Add a notice about pending URL
                const apiKeySection = document.getElementById('api-key-section');
                const notice = document.createElement('p');
                notice.style.cssText = 'text-align: center; color: #2563eb; margin-top: 20px;';
                notice.textContent = 'URL detected - will convert after API key is saved';
                apiKeySection.appendChild(notice);
            }
        }
    } catch (error) {
        console.error('Error checking API key:', error);
        // Hide loading on error
        document.getElementById('initial-loading').style.display = 'none';
        document.getElementById('main-container').style.display = 'block';
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
            
            // Check if we have a pending URL conversion
            if (pendingUrlConversion) {
                // Set the URL and start conversion
                document.getElementById('url-input').value = pendingUrlConversion;
                
                // Hide upload UI and show progress
                document.getElementById('upload-area').style.display = 'none';
                document.getElementById('url-input-container').style.display = 'none';
                document.getElementById('progress-container').style.display = 'block';
                document.getElementById('progress-fill').style.width = '30%';
                document.getElementById('status-text').textContent = 'Fetching URL...';
                
                // Start conversion immediately
                handleURL();
            }
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
                            // Reset page title
                            document.title = 'Document to Markdown Converter';
                        } else if (data.error) {
                            showError(data.error);
                            // Reset page title
                            document.title = 'Document to Markdown Converter';
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
                // Reset page title
                document.title = 'Document to Markdown Converter';
            } else if (data.error) {
                showError(data.error);
                eventSource.close();
                // Reset page title
                document.title = 'Document to Markdown Converter';
            }
        };

        eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            showError('Failed to process URL. Please check if the site is accessible.');
            eventSource.close();
            // Reset page title
            document.title = 'Document to Markdown Converter';
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

// Removed checkForURLParameter function - URL parameters are now handled in window.onload

// Store original page state for exiting reader mode
let originalBodyContent = null;
let isInReaderMode = false;

function openReaderMode() {
    if (!convertedMarkdown) {
        showError('No content to display in reader mode');
        return;
    }
    
    // Save current body content
    originalBodyContent = document.body.innerHTML;
    isInReaderMode = true;
    
    // Create reader mode content
    const readerContent = `
        <style id="reader-mode-styles">
            @font-face {
                font-family: 'Departure Mono';
                src: url('/static/font/DepartureMono-Regular.woff2') format('woff2'),
                     url('/static/font/DepartureMono-Regular.woff') format('woff'),
                     url('/static/font/DepartureMono-Regular.otf') format('opentype');
                font-weight: 400;
                font-style: normal;
            }
            body.reader-mode {
                margin: 0;
                padding: 0;
                background-color: white;
                color: #333;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.7;
                font-size: 16px;
            }
            .reader-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 40px 20px;
                background-color: white;
                min-height: 100vh;
            }
            .reader-controls {
                position: fixed;
                top: 20px;
                right: 20px;
                display: flex;
                gap: 10px;
                z-index: 1000;
            }
            .reader-button {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-family: 'Departure Mono', monospace;
                font-size: 14px;
                transition: background-color 0.2s;
            }
            .reader-button:hover {
                background-color: #1d4ed8;
            }
            .reader-mode h1, .reader-mode h2, .reader-mode h3, .reader-mode h4, .reader-mode h5, .reader-mode h6 {
                font-weight: bold;
            }
            .reader-mode h1 { font-size: 2em; margin: 0.67em 0; }
            .reader-mode h2 { font-size: 1.5em; margin: 0.75em 0; }
            .reader-mode h3 { font-size: 1.17em; margin: 0.83em 0; }
            .reader-mode h4 { font-size: 1em; margin: 1.12em 0; }
            .reader-mode h5 { font-size: 0.83em; margin: 1.5em 0; }
            .reader-mode h6 { font-size: 0.75em; margin: 1.67em 0; }
            .reader-mode p {
                margin: 1em 0;
            }
            .reader-mode blockquote {
                margin: 1em 0;
                padding-left: 1em;
                border-left: 4px solid #e5e7eb;
                color: #6b7280;
            }
            .reader-mode code {
                background-color: #f3f4f6;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: monospace;
                font-size: 0.9em;
            }
            .reader-mode pre {
                background-color: #f3f4f6;
                padding: 12px;
                border-radius: 4px;
                overflow-x: auto;
            }
            .reader-mode pre code {
                background-color: transparent;
                padding: 0;
            }
            .reader-mode ul, .reader-mode ol {
                margin: 1em 0;
                padding-left: 2em;
            }
            .reader-mode li {
                margin: 0.5em 0;
            }
            .reader-mode a {
                color: #2563eb;
                text-decoration: underline;
            }
            .reader-mode a:hover {
                color: #1d4ed8;
            }
            .reader-mode hr {
                border: none;
                border-top: 1px solid #e5e7eb;
                margin: 2em 0;
            }
            .reader-mode table {
                border-collapse: collapse;
                margin: 1em 0;
            }
            .reader-mode th, .reader-mode td {
                border: 1px solid #e5e7eb;
                padding: 8px;
            }
            .reader-mode th {
                background-color: #f3f4f6;
                font-weight: bold;
            }
            @media (max-width: 768px) {
                body.reader-mode {
                    font-size: 16px;
                }
                .reader-container {
                    padding: 20px 15px;
                }
                .reader-controls {
                    top: 10px;
                    right: 10px;
                }
            }
        </style>
        <div class="reader-controls">
            <button class="reader-button" onclick="exitReaderMode()">Exit Reader Mode</button>
        </div>
        <div class="reader-container" id="reader-content"></div>
    `;
    
    // Replace body content and add reader mode class
    document.body.innerHTML = readerContent;
    document.body.className = 'reader-mode';
    
    // Convert markdown to HTML and display
    document.getElementById('reader-content').innerHTML = marked.parse(convertedMarkdown);
    
    // Add keyboard shortcut to exit
    document.addEventListener('keydown', handleReaderModeKeydown);
}

function exitReaderMode() {
    if (!isInReaderMode || !originalBodyContent) return;
    
    // Restore original content
    document.body.innerHTML = originalBodyContent;
    document.body.className = '';
    
    // Re-attach event listeners and restore state
    window.onload = null; // Prevent re-initialization
    isInReaderMode = false;
    originalBodyContent = null;
    
    // Remove reader mode keyboard listener
    document.removeEventListener('keydown', handleReaderModeKeydown);
}

function handleReaderModeKeydown(e) {
    if (e.key === 'Escape') {
        exitReaderMode();
    }
}