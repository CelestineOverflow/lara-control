<!-- <script lang="ts">
    import { codeToHtml } from 'shiki'
    import { onMount } from 'svelte'

    export let code = 'const a = 1' // input code
    export let lang = 'javascript'
    export let theme = 'vitesse-dark'

    let container : HTMLElement;

    async function highlight() {
        const html = await codeToHtml(code, {
        lang: lang,
        theme: theme
        })
        container.innerHTML = html
    }

    onMount(() => {
        highlight()
    })
</script>


<div bind:this={container}/> -->
