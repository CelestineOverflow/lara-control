<!-- <script lang="ts">
    import { Terminal } from "@xterm/xterm";
    import { FitAddon } from "@xterm/addon-fit";
    import { onMount, onDestroy, createEventDispatcher } from "svelte";

    let terminalDiv: HTMLDivElement;
    let terminal: Terminal;
    let fitAddon: FitAddon;
    let resizeObserver: ResizeObserver;
    const dispatch = createEventDispatcher();

    onMount(() => {
        terminal = new Terminal({
            cursorBlink: true,
            scrollback: 50, // Limit the scrollback buffer to 100 lines
            theme: {
                background: "#000000", // Dark background
                foreground: "#FFFFFF", // White text
            },
            
        });
        terminal.onBell(() => dispatch('bell'));
		terminal.onBinary((data) => dispatch('binary', data));
		terminal.onCursorMove(() => dispatch('cursormove'));
		terminal.onData((data) => dispatch('data', data));
		terminal.onKey((data) => dispatch('key', data));
		terminal.onLineFeed(() => dispatch('linefeed'));
		terminal.onRender((data) => dispatch('render', data));
		terminal.onWriteParsed(() => dispatch('writeparsed'));
		terminal.onResize((data) => dispatch('resize', data));
		terminal.onScroll((data) => dispatch('scroll', data));
		terminal.onSelectionChange(() => dispatch('selectionchange'));
		terminal.onTitleChange((data) => dispatch('titlechange', data));


        fitAddon = new FitAddon();
        terminal.loadAddon(fitAddon);
        dispatch('load', { terminal });
        terminal.open(terminalDiv);
        fitAddon.fit(); // Initial fit

        prompt();
        terminal.focus();

        // Handle user input
        let command = "";

        terminal.onData((data) => {
            switch (data) {
                case "\r": // Enter
                    terminal.write("\r\n");
                    executeCommand(command);
                    command = "";
                    prompt();
                    break;
                case "\u007F": // Backspace (DEL)
                    // Don't delete the prompt
                    if (command.length > 0) {
                        terminal.write("\b \b");
                        command = command.slice(0, -1);
                    }
                    break;
                default:
                    // For all other printable characters
                    if (data >= " " && data <= "~") {
                        terminal.write(data);
                        command += data;
                    }
                    break;
            }
        });

        // Handle terminal resize
        resizeObserver = new ResizeObserver(() => {
            fitAddon.fit();
        });
        resizeObserver.observe(terminalDiv);
    });

    onDestroy(() => {
        if (resizeObserver) {
            resizeObserver.disconnect();
        }
        terminal.dispose();
    });

    let colorsPalleter = {
        "green": "\x1b[32m",
        "red": "\x1b[31m",
        "yellow": "\x1b[33m",
        "blue": "\x1b[34m",
        "magenta": "\x1b[35m",
        "cyan": "\x1b[36m",
        "white": "\x1b[37m",
        "reset": "\x1b[0m",
    };
    
    function prompt() {
        terminal.write(colorsPalleter.green + "$ " + colorsPalleter.reset);
    }

    function executeCommand(cmd: string) {
        //check if command is clear
        if (cmd === "clear") {
            console.log("Clearing terminal");
            terminal.clear();
            prompt();
            return;
        }
        terminal.writeln(`Running: ${colorsPalleter.yellow}${cmd}${colorsPalleter.reset}`);
    }

</script>

<div bind:this={terminalDiv}></div>

<style>
    :global(.xterm-viewport) {
        overflow-y: auto;
    }
</style>
 -->
