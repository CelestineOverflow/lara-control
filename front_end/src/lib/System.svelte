<script lang="ts">
	import { daemonStatusJson } from './robotics/coordinate.svelte';
	import { reboot, restartDeployer } from './robotics/laraapi';

	async function kill_proccess(script_name: string) {
		const url = `http://192.168.2.209:8765/kill_process?script_name=${script_name}`;
		try {
			const response = await fetch(url);
			if (response.ok) {
				console.log('Process killed successfully.');
			} else {
				console.error('Failed to kill process.', response.status);
			}
		} catch (error) {
			console.error('Error killing process:', error);
		}
	}

	async function restart_process(script_name: string) {
		const url = `http://192.168.2.209:8765/restart_process?script_name=${script_name}`;
		try {
			const response = await fetch(url);
			if (response.ok) {
				console.log('Process restarted successfully.');
			} else {
				console.error('Failed to restart process.', response.status);
			}
		} catch (error) {
			console.error('Error restarting process:', error);
		}
	}

	async function show_process(script_name: string) {
		const url = `http://192.168.2.209:8765/show_process?script_name=${script_name}`;
		try {
			const response = await fetch(url);
			if (response.ok) {
				console.log('Process restarted successfully.');
			} else {
				console.error('Failed to restart process.', response.status);
			}
		} catch (error) {
			console.error('Error restarting process:', error);
		}
	}




	let status = $state('✅'); // Default status
	daemonStatusJson.subscribe((value) => {
		//check if all processes are running or some or none

		if (value) {
			const allRunning = Object.values(value).every((process) => process.running);
			if (allRunning) {
				status = '✅'; // All processes are running
			} else {
				const someRunning = Object.values(value).some((process) => process.running);
				status = someRunning ? '⚠️' : '❌'; // Some processes are running or none
			}
		} else {
			status = '❌'; // No data available
		}
	});
</script>

<div class="tooltip tooltip-bottom" data-tip="manage system processes">
	<div class="dropdown dropdown-bottom">
		<div tabindex="0" role="button" class="btn m-1">System Status {status}</div>
		<div class="dropdown-content menu bg-base-100 rounded-box z-1 w-202 p-1 shadow-sm">
			
			<table class="table">
				<thead>
					<tr>
						<th>Script Name</th>
						<th>PID</th>
						<th>Running</th>
						<th>Debug Mode</th>
					</tr>
				</thead>
				<tbody>
					{#if $daemonStatusJson}
						{#each Object.entries($daemonStatusJson) as [key, value]}
							<tr>
								<td>{key}</td>
								<td>{value.pid}</td>
								<td>{value.running ? '✅' : '❌'}</td>
								<td>{value.debug ? '✅' : '❌'}</td>
								<td>
									<button class="btn btn-sm btn-error" onclick={() => kill_proccess(key)}
										>Kill</button
									>
									<button class="btn btn-sm btn-warning" onclick={() => restart_process(key)}
										>Restart</button
									>
									<button class="btn btn-sm btn-info" onclick={() => show_process(key)}
										>Show</button
									>
								</td>
							</tr>
						{/each}
					{/if}
				</tbody>
			</table>
			<div class="flex justify-center">
				
			<div class="tooltip tooltip-bottom" data-tip="Redeploy proprietary Neura Robotics control code on the robot arm PC. This process may take a while. You will need to press the white button on the control box afterwards.">
				<button class="btn btn-warning" onclick={() => restartDeployer()}>Restart Robot Arm Code</button>
				</div>
			<div class="tooltip tooltip-bottom" data-tip="This will restart the robot arm pc. This process may take a while. You will need to press the white button on the control box afterwards.">
				<button class="btn btn-error" onclick={() => reboot()}>Restart Robot Arm Pc</button>
				</div>
			</div>
		</div>
	</div>
</div>
