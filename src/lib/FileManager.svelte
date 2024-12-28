<script lang="ts">
    import { writable } from "svelte/store";
  
    // Placeholder folder structure (JSON description)
    const folderStructure = {
      name: "root",
      type: "folder",
      contents: [
        { name: "Documents", type: "folder", contents: [] },
        { name: "Images", type: "folder", contents: [{ name: "photo.png", type: "file" }] },
        { name: "Notes.txt", type: "file" },
      ],
    };
  
    let selectedFile: string = "";
    let currentFolder = writable(folderStructure);
  
    function selectFile(item) {
      if (item.type === "file") {
        selectedFile = item.name;
      }
    }
  
    function openFolder(folder) {
      currentFolder.set(folder);
    }
  </script>
  
  <div class="file-manager">
    <ul>
      {#each $currentFolder.contents as item}
        <li>
          {#if item.type === "folder"}
            <div class="folder" on:click={() => openFolder(item)}>
              <i class="icon-folder"></i> {item.name}
            </div>
          {:else}
            <div class="file" on:click={() => selectFile(item)}>
              <i class="icon-file"></i> {item.name}
            </div>
          {/if}
        </li>
      {/each}
    </ul>
  
    {#if selectedFile}
      <div class="selected-file">
        Selected File: <strong>{selectedFile}</strong>
      </div>
    {/if}
  </div>
  
  <style>
    .file-manager {
      background-color: #2d2d2d;
      color: #ffffff;
      padding: 10px;
      border-radius: 8px;
      width: 300px;
    }
  
    ul {
      list-style-type: none;
      padding: 0;
    }
  
    li {
      margin: 5px 0;
    }
  
    .folder, .file {
      cursor: pointer;
      padding: 8px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      background-color: #3e3e3e;
    }
  
    .folder:hover, .file:hover {
      background-color: #555555;
    }
  
    .icon-folder::before {
      content: "📁";
      margin-right: 10px;
    }
  
    .icon-file::before {
      content: "📄";
      margin-right: 10px;
    }
  
    .selected-file {
      margin-top: 20px;
      font-size: 0.9rem;
      background-color: #444444;
      padding: 10px;
      border-radius: 4px;
    }
  </style>