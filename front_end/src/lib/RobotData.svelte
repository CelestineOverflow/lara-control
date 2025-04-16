<script lang="ts">
    import { robotJoints} from "$lib/robotics/coordinate.svelte";
    let toggle = "";
</script>





<div class="grid grid-cols-1">
    <!-- <Switch bind:value={toggle} label="Enable dark mode" fontSize={24} design="slider" />
    {toggle} -->
    {#if toggle = "on"}
    <p1>Cartesian X {($robotJoints.x * 1000).toFixed(2)} mm</p1>
    <p1>Cartesian Y {($robotJoints.y * 1000).toFixed(2)} mm</p1>
    <p1>Cartesian Z {($robotJoints.z * 1000).toFixed(2)} mm</p1>
    <p1>Cartesian A {(($robotJoints.a * 180 / Math.PI) ).toFixed(2)}°</p1>
    <p1>Cartesian B {(($robotJoints.b * 180 / Math.PI) ).toFixed(2)}°</p1>
    <p1>Cartesian C {(($robotJoints.c * 180 / Math.PI) ).toFixed(2)}°</p1>
    {:else}
    <p1>J1 {$robotJoints.joint1.toFixed(2)}</p1>
    <p1>J2 {$robotJoints.joint2.toFixed(2)}</p1>
    <p1>J3 {$robotJoints.joint3.toFixed(2)}</p1>
    <p1>J4 {$robotJoints.joint4.toFixed(2)}</p1>
    <p1>J5 {$robotJoints.joint5.toFixed(2)}</p1>
    <p1>J6 {$robotJoints.joint6.toFixed(2)}</p1>
    {/if}
  </div>