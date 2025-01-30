<script>
	import Accordion from "$lib/Accordion.svelte";
</script>

<Accordion>
	<span slot="head">This is my header</span>
	<div slot="details">
		<p>
			These are the details.
		</p>
	</div>
</Accordion>

<Accordion open={true}>
	<span slot="head">This is my header number two, it's quite long so should span multiple lines (if not: please resize the window!)</span>
	<div slot="details">
		<p>
			These are the second details.
		</p>
		<p>
			This can naturally span multiple lines.
		</p>
	</div>
</Accordion>

<Accordion>
	<span slot="head">This is a header for a table.</span>
	<div slot="details">
		
<table>
	<thead>
		<tr>
			<th>Company</th>
			<th>Contact</th>
			<th>Country</th>
		</tr>
	</thead>
  <tbody>
		<tr>
			<td>Alfreds Futterkiste</td>
			<td>Maria Anders</td>
			<td>Germany</td>
		</tr>
		<tr>
			<td>Centro comercial Moctezuma</td>
			<td>Francisco Chang</td>
			<td>Mexico</td>
		</tr>
		<tr>
			<td>Ernst Handel</td>
			<td>Roland Mendel</td>
			<td>Austria</td>
		</tr>
		<tr>
			<td>Island Trading</td>
			<td>Helen Bennett</td>
			<td>UK</td>
		</tr>
		<tr>
			<td>Laughing Bacchus Winecellars</td>
			<td>Yoshi Tannamuri</td>
			<td>Canada</td>
		</tr>
		<tr>
			<td>Magazzini Alimentari Riuniti</td>
			<td>Giovanni Rovelli</td>
			<td>Italy</td>
		</tr>
	</tbody>
</table>
	</div>
</Accordion>