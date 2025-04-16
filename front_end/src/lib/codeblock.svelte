<script lang="ts">
    import { onMount } from 'svelte';
    import Prism from 'prismjs';
    import 'prismjs/components/prism-python';
    import 'prismjs/themes/prism-tomorrow.css';
    export let code_file = 'test.py';

    let pythonCode = '';
    let highlightedCode = '';

    // Function to highlight the code using Prism
    function highlight() {
        highlightedCode = Prism.highlight(pythonCode, Prism.languages.python, 'python');
    }

    // Fetch the file from the static directory
    async function loadFile() {
        const response = await fetch(code_file);
        if (response.ok) {
            pythonCode = await response.text();
            highlight();
        } else {
            console.error('Failed to load /test.py');
        }
    }

    // Copy code to clipboard
    function copyToClipboard() {
        navigator.clipboard.writeText(pythonCode);
        const copyBtn = document.getElementById('copy-btn');
        if (copyBtn) {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            setTimeout(() => {
                copyBtn.textContent = originalText;
            }, 2000);
        }
    }

    // Load file and highlight code when component mounts
    onMount(() => {
        loadFile();
    });
</script>

<div>
    <div class="bg-gray-800 rounded-lg overflow-hidden">
        <div class="bg-gray-700 px-4 py-2 flex justify-between items-center">
            <div class="flex items-center">
                <span class="text-sm font-medium">Python Code</span>
            </div>
            <button 
                id="copy-btn"
                class="text-xs bg-blue-600 px-2 py-1 rounded hover:bg-blue-700 transition-colors"
                on:click={copyToClipboard}
            >
                Copy
            </button>
        </div>
        <pre class="text-gray-200 p-4 text-sm overflow-auto h-[500px] max-h-[calc(100vh-500px)] overflow-y-auto">
            <code class="language-python">{@html highlightedCode}</code>
        </pre>
    </div>
</div>


<style>
    pre {
        white-space: pre-line;
        
    }
</style>