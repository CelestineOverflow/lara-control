<script lang="ts">
    import { onMount } from "svelte";
    import Apriltag from "./Apriltag.svelte";
    let video: HTMLVideoElement;
    let canvas: HTMLCanvasElement;
    let outputCanvas: HTMLCanvasElement;
    let stream: MediaStream | null = null;
    onMount(async () => {
        const constraints = {
            video: {
                // 4K resolution
                // width: { ideal: 4096 },
                // height: { ideal: 2160 },
                // 1080p resolution
                width: { ideal: 1920 },
                height: { ideal: 1080 },
            },
        };
        navigator.mediaDevices.getUserMedia(constraints).then((the_stream) => {
            video.srcObject = the_stream;
            console.log(the_stream.getVideoTracks()[0].getSettings());
            stream = the_stream;
        });
        //     try {
        //         let ctx = canvas.getContext('2d');
        //         ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        //         // Read the frame into OpenCV
        //         let src = cv.imread(canvas);
        //         let dst = new cv.Mat();
        //         // Convert the image to grayscale
        //         cv.cvtColor(src, dst, cv.COLOR_RGBA2GRAY);
        //         // Detect Checkerboard
        //         let corners = new cv.Mat();
        //         let patternSize = new cv.Size(9, 6);
        //         //display available functions for cv
        //         console.log(Object.keys(cv));
        //         // let found = cv.findChessboardCornersSB(dst, patternSize, corners);
        //         // Display the processed frame
        //         cv.imshow(outputCanvas, dst);
        //         // Clean up
        //         src.delete();
        //         dst.delete();
        //         // Request the next frame
        //         requestAnimationFrame(processVideo);
        //     } catch (err) {
        //         console.error(err);
        //     }
        // }
        // // Start processing
        // processVideo();
    });

    let enabled = false;


 </script>
 <!-- svelte-ignore a11y-media-has-caption -->
 <video bind:this={video}   style="width: 50%;" autoplay></video>


 <button on:click={() => enabled = !enabled}>{enabled ? "Disable" : "Enable"}</button>


{#if enabled}
    <Apriltag {stream}  />
{/if}
