<script>
    // @ts-nocheck
    import { onMount } from "svelte";
    import * as Comlink from "comlink";
    import * as Base64 from "./base64.js";
    import * as THREE from "three";
    import {
        AprilTagRelativePosition,
        AprilTagInView,
        ApriltagDetection,
        AprilTagRotation
    } from "$lib/coordinate";
    import { degToRad } from "three/src/math/MathUtils.js";
    // Accept tag size as a prop
    export let stream;
    let canvas;
    let videoElement;
    let is_there_a_tag = false;
    let ctx;
    let svg_detected;
    let openCVHasLoaded = false;
    let crosshair;
    let imagePoints;
    let objectPoints;
    let cameraMatrix;
    let distCoeffs;
    const tagSize = 0.2;
    const calibration_data = {
        mtx: [
            [654.5952480969623, 0.0, 500.01278566397866],
            [0.0, 654.5876733792369, 498.8225067121044],
            [0.0, 0.0, 1.0],
        ],
        dist: [
            [
                0.00013215199755571149, -0.022527581164393257,
                -0.0007325212200046806, -0.0003291560768781044,
                0.022630956877425255,
            ],
        ],
    };

    function delay(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    function setupPnP_Params() {
        objectPoints = cv.matFromArray(4, 1, cv.CV_64FC3, [
            -tagSize / 2,
            -tagSize / 2,
            0,
            tagSize / 2,
            -tagSize / 2,
            0,
            tagSize / 2,
            tagSize / 2,
            0,
            -tagSize / 2,
            tagSize / 2,
            0,
        ]);
        cameraMatrix = cv.matFromArray(
            3,
            3,
            cv.CV_64F,
            calibration_data.mtx.flat(),
        );
        distCoeffs = cv.matFromArray(
            1,
            5,
            cv.CV_64F,
            calibration_data.dist.flat(),
        );
    }

    function runSolvePnP(detection) {
        // Prepare imagePoints
        imagePoints = cv.matFromArray(4, 1, cv.CV_64FC2, [
            detection.corners[0].x,
            detection.corners[0].y,
            detection.corners[1].x,
            detection.corners[1].y,
            detection.corners[2].x,
            detection.corners[2].y,
            detection.corners[3].x,
            detection.corners[3].y,
        ]);

        // Prepare rvec and tvec as output
        const rvec = new cv.Mat();
        const tvec = new cv.Mat();

        // Solve PnP
        const success = cv.solvePnP(
            objectPoints,
            imagePoints,
            cameraMatrix,
            distCoeffs,
            rvec,
            tvec,
        );

        if (success) {
            AprilTagRelativePosition.set(
            new THREE.Vector3(
                tvec.data64F[0],
                tvec.data64F[2],
                tvec.data64F[1],
            ),
            );
            //convert rvec to rotation matrix
            const rmat = new cv.Mat();
            cv.Rodrigues(rvec, rmat);
            const rotationMatrix = new THREE.Matrix4();
            rotationMatrix.set(
                rmat.data64F[0],
                rmat.data64F[1],
                rmat.data64F[2],
                0,
                rmat.data64F[3],
                rmat.data64F[4],
                rmat.data64F[5],
                0,
                rmat.data64F[6],
                rmat.data64F[7],
                rmat.data64F[8],
                0,
                0,
                0,
                0,
                1,
            );
            let quaternion = new THREE.Quaternion();
            quaternion.setFromRotationMatrix(rotationMatrix);
            quaternion = new THREE.Quaternion(quaternion.y, -quaternion.z, -quaternion.x, quaternion.w);
            // console.log('q x: ', quaternion.x, 'q y: ', quaternion.y, 'q z: ', quaternion.z, 'q w: ', quaternion.w);
            quaternion.multiply(new THREE.Quaternion(0, 0, -1, 0).invert());
            AprilTagRotation.set(quaternion);
        }
        //

        // Clean up
        rvec.delete();
        tvec.delete();
    }

    onMount(async () => {
        await new Promise((resolve) => {
            const checkOpenCV = setInterval(() => {
                if (window.cv) {
                    clearInterval(checkOpenCV);
                    window.cv["onRuntimeInitialized"] = () => {
                        console.log("OpenCV loaded successfully");

                        resolve();
                    };
                }
            }, 100);
        });
        await setupCamera();
        await setupPnP_Params();

        svg_detected = new Image();
        svg_detected.src =
            "./svg/location_searching_24dp_E8EAED_FILL0_wght400_GRAD0_opsz24.svg";
        crosshair = new Image();
        crosshair.src =
            "./svg/crop_free_24dp_E8EAED_FILL0_wght400_GRAD0_opsz24.svg";
        await svg_detected.decode();
        await crosshair.decode();
        await delay(3000);
        await startApriltag();
    });

    async function setupCamera() {
        videoElement = document.createElement("video");
        videoElement.autoplay = true;
        videoElement.playsInline = true;
        if (stream) {
            videoElement.srcObject = stream;
            // Wait for the video metadata to load to get the resolution
            await new Promise(
                (resolve) => (videoElement.onloadedmetadata = resolve),
            );

            // Set the canvas size based on the video resolution once
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
        } else {
            console.error("No stream provided");
        }
    }

    async function startApriltag() {
        const Apriltag = Comlink.wrap(new Worker("./apriltag/apriltag.js"));
        window.apriltag = await new Apriltag(
            Comlink.proxy(async () => {
                window.apriltag.set_tag_size(0, 0.02);
                console.log("Apriltag loaded");
                window.requestAnimationFrame(processFrame);
            }),
        );
        ctx = canvas.getContext("2d");
        ctx.willReadFrequently = true;
    }

    function draw() {
        ctx.drawImage(svg_detected, 10, 10, 50, 50);

        if ($AprilTagInView) {
            ctx.fillStyle = "white";
            ctx.font = "50px Verdana";
            ctx.fillText("detected", 70, 50);
            //draw a dot
            ctx.fillStyle = "green";
            ctx.beginPath();
            ctx.arc(35, 35, 10, 0, 2 * Math.PI);
            ctx.fill();
            //draw cross air on the screen
            ctx.lineWidth = 0.1; // Set the line width
            const crosshairSize = canvas.width / 4; // Adjust the size as needed
            ctx.drawImage(
                crosshair,
                canvas.width / 2 - crosshairSize / 2,
                canvas.height / 2 - crosshairSize / 2,
                crosshairSize,
                crosshairSize,
            );
        }
        if ($ApriltagDetection && $ApriltagDetection.length > 0) {
            $ApriltagDetection.forEach((det) => {
                // Draw the corners
                ctx.fillStyle = "red";
                const corners = det.corners;
                ctx.closePath();
                ctx.stroke();

                // Draw the center
                ctx.fillStyle = "blue";
                ctx.beginPath();
                ctx.lineWidth = 50;
                ctx.arc(det.center.x, det.center.y, 5, 0, 2 * Math.PI);
                ctx.fill();

                // Draw the tag ID
                ctx.fillStyle = "red";
                ctx.font = "40px Arial";
                ctx.fillText(
                    "ID: " + det.id,
                    det.center.x + 10,
                    det.center.y + 10,
                );
                // Draw the pose
                // ctx.fillStyle = "red";
                // ctx.font = "60px Arial";
                // const position = $AprilTagRelativePosition;
                // ctx.fillText(
                //     `X: ${position.x.toFixed(2)}, Y: ${position.y.toFixed(2)}, Z: ${position.z.toFixed(2)}`,
                //     det.center.x + 10,
                //     det.center.y + 50,
                // );
                // Draw Corners Lines
                //line width 2px
                ctx.lineWidth = 2;
                ctx.strokeStyle = "red";
                ctx.beginPath();
                ctx.moveTo(corners[0].x, corners[0].y);
                ctx.lineTo(corners[1].x, corners[1].y);
                ctx.lineTo(corners[2].x, corners[2].y);
                ctx.lineTo(corners[3].x, corners[3].y);
                ctx.lineTo(corners[0].x, corners[0].y);
                ctx.stroke();

            });
        }
    }

    async function processFrame() {
        if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
            ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

            const imageData = ctx.getImageData(
                0,
                0,
                canvas.width,
                canvas.height,
            );
            const grayscalePixels = new Uint8Array(
                canvas.width * canvas.height,
            );
            draw(ctx);
            const pixels = imageData.data;
            for (let i = 0, j = 0; i < pixels.length; i += 4, j++) {
                const grayscale =
                    (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
                grayscalePixels[j] = grayscale;
            }

            const detections = await window.apriltag.detect(
                grayscalePixels,
                canvas.width,
                canvas.height,
            );
            if (detections.length > 0) {
                AprilTagInView.set(true);
                runSolvePnP(detections[0]);
            } else {
                AprilTagInView.set(false);
            }
            ApriltagDetection.set(detections);
        }

        window.requestAnimationFrame(processFrame);
    }
</script>

<!-- <canvas bind:this={canvas} style="display: none;"></canvas> -->
<canvas bind:this={canvas} style="width: 50%; "></canvas>
<svelte:head>
    <script src="https://docs.opencv.org/4.5.4/opencv.js" async></script>
</svelte:head>
