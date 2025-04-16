<script lang="ts">
    import Codeblock from "$lib/codeblock.svelte";

    const api_download_url = 'http://192.168.2.209:1442/api_download';

    function downloadFile() {
        const link = document.createElement('a');
        link.href = api_download_url;
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

</script>

<main class="container mx-auto p-6">
    <h1 class="text-4xl font-bold mb-4">Getting Started with LabHandler 🚀</h1>
    <p class="text-lg text-gray-700 mb-6 text-white">
        Get the LabHandler app running on your local machine.
    </p>
    <button
        class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-5 rounded-md shadow transition-colors"
        on:click={downloadFile}
    >
        Download LabHandler API
    </button>
    <Codeblock code_file="/python-examples/basic.py" />
    <div></div>
    <h2 class="text-2xl font-bold mb-4">API Endpoints</h2>
    <p class="text-lg text-gray-700 mb-6 text-white">
        The LabHandler API provides several methods to interact with the system. Below are some of the key ones:
    </p>
    <Codeblock code_file="/python-examples/control-user.py" />

</main>
