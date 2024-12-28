<script lang="ts">
    import ComponentTest from "$lib/components/ComponentTest.svelte";
    import Highlight from "$lib/highlight.svelte";
    import TestSplitPanels from "$lib/TestSplitPanels.svelte";
</script>

<ComponentTest title={`Process Manager`}
    ><table class="table-auto">
        <thead>
            <tr>
                <th>Song</th>
                <th>Artist</th>
                <th>Year</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>The Sliding Mr. Bones (Next Stop, Pottersville)</td>
                <td>Malcolm Lockyer</td>
                <td>1961</td>
            </tr>
            <tr>
                <td>Witchy Woman</td>
                <td>The Eagles</td>
                <td>1972</td>
            </tr>
            <tr>
                <td>Shining Star</td>
                <td>Earth, Wind, and Fire</td>
                <td>1975</td>
            </tr>
        </tbody>
    </table></ComponentTest
>
