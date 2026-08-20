import{W as d}from"./index-DLhKVP8V.js";const u="/api/ubme";async function b(e,r){const o=await fetch(`${u}${e}`,{credentials:"include",headers:{"Content-Type":"application/json",...r==null?void 0:r.headers},...r}),m=await o.json();if(!o.ok)throw new Error(m.error||`HTTP ${o.status}`);return m}async function c(){return(await b("/types")).data}async function p(){return(await b("/navigation")).data}const f=`
.ubme-builder { padding: 1.5rem; max-width: 1200px; margin: 0 auto; }
.ubme-builder-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.5rem; }
.ubme-builder-header h2 { margin: 0; font-size: 1.25rem; }
.ubme-builder-title-row { display: flex; align-items: center; gap: 0.75rem; }
.ubme-header-actions { display: flex; gap: 0.5rem; }

.ubme-module-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
.ubme-module-card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; cursor: pointer; transition: all 0.2s; display: flex; gap: 1rem; }
.ubme-module-card:hover { border-color: #6366f1; transform: translateY(-2px); }
.ubme-module-icon { width: 48px; height: 48px; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; flex-shrink: 0; }
.ubme-module-info { flex: 1; min-width: 0; }
.ubme-module-info h3 { margin: 0 0 0.25rem; font-size: 1rem; }
.ubme-module-info p { margin: 0 0 0.5rem; font-size: 0.8rem; color: #94a3b8; }
.ubme-module-meta { display: flex; gap: 0.75rem; font-size: 0.75rem; color: #64748b; }
.ubme-template-source { background: #6366f1; color: #fff; padding: 0.125rem 0.375rem; border-radius: 4px; font-size: 0.7rem; }

.ubme-template-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1rem; }
.ubme-template-card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.25rem; cursor: pointer; transition: all 0.2s; display: flex; gap: 1rem; }
.ubme-template-card:hover { border-color: #10b981; }
.ubme-template-icon { font-size: 2rem; }
.ubme-template-info h3 { margin: 0 0 0.25rem; }
.ubme-template-info p { margin: 0 0 0.5rem; font-size: 0.85rem; color: #94a3b8; }
.ubme-template-badge { background: #1e293b; padding: 0.125rem 0.375rem; border-radius: 4px; border: 1px solid #334155; font-size: 0.7rem; margin-right: 0.5rem; }
.ubme-template-count { color: #64748b; font-size: 0.75rem; }

.ubme-module-tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.ubme-tab { padding: 0.5rem 1rem; background: transparent; border: 1px solid transparent; border-radius: 0.5rem; color: #94a3b8; cursor: pointer; font-size: 0.875rem; }
.ubme-tab.active { background: #1e293b; border-color: #334155; color: #fff; }

.ubme-object-types { display: flex; flex-direction: column; gap: 0.75rem; }
.ubme-object-type-card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; }
.ubme-ot-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
.ubme-ot-header strong { font-size: 1rem; }
.ubme-badge { background: #334155; padding: 0.125rem 0.375rem; border-radius: 4px; font-size: 0.75rem; color: #94a3b8; }
.ubme-field-count { font-size: 0.75rem; color: #64748b; margin-left: auto; }
.ubme-ot-fields { display: flex; flex-wrap: wrap; gap: 0.375rem; }
.ubme-field-chip { background: #0f172a; padding: 0.25rem 0.5rem; border-radius: 0.375rem; font-size: 0.75rem; }
.ubme-field-type { color: #64748b; }
.ubme-more-fields { color: #64748b; font-size: 0.75rem; display: flex; align-items: center; }

.ubme-new-module-form { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1rem; max-width: 500px; }
.ubme-new-module-form h3 { margin: 0 0 1rem; }
.ubme-form-row { margin-bottom: 0.75rem; }
.ubme-form-row label { display: block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 0.25rem; }
.ubme-form-row input, .ubme-form-row select, .ubme-form-row textarea { width: 100%; }
.ubme-form-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.ubme-checkbox-row { display: flex; gap: 1rem; margin: 0.75rem 0; }
.ubme-checkbox-row label { display: flex; align-items: center; gap: 0.375rem; font-size: 0.8rem; color: #94a3b8; cursor: pointer; }
.ubme-checkbox-label { display: flex; align-items: center; gap: 0.25rem; font-size: 0.75rem; }

.ubme-btn-primary { background: #6366f1; color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer; font-size: 0.875rem; }
.ubme-btn-primary:hover { background: #4f46e5; }
.ubme-btn-secondary { background: transparent; color: #94a3b8; border: 1px solid #334155; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer; font-size: 0.875rem; }
.ubme-btn-secondary:hover { border-color: #6366f1; color: #fff; }
.ubme-edit-btn, .ubme-delete-btn { background: transparent; border: none; cursor: pointer; padding: 0.25rem; font-size: 0.875rem; }
.ubme-delete-btn:hover { opacity: 0.7; }
.ubme-add-ot-btn, .ubme-add-field-btn, .ubme-add-btn { background: transparent; border: 1px dashed #334155; border-radius: 0.5rem; padding: 0.75rem; color: #6366f1; cursor: pointer; font-size: 0.875rem; text-align: center; margin-top: 0.5rem; }
.ubme-add-ot-btn:hover, .ubme-add-field-btn:hover, .ubme-add-btn:hover { border-color: #6366f1; }

.ubme-ot-editor { padding: 1.5rem; max-width: 900px; margin: 0 auto; }
.ubme-ot-settings { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; margin-bottom: 1rem; }
.ubme-field-editor-row { display: flex; align-items: center; gap: 0.75rem; background: #0f172a; padding: 0.5rem 0.75rem; border-radius: 0.5rem; margin-bottom: 0.375rem; }
.ubme-field-editor-icon { width: 24px; text-align: center; font-size: 0.875rem; }
.ubme-field-editor-type { color: #64748b; font-size: 0.75rem; flex: 1; }
.ubme-field-editor-modal { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.ubme-field-editor-form { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; width: 400px; max-height: 80vh; overflow-y: auto; }
.ubme-field-editor-form h4 { margin: 0 0 1rem; }

.ubme-view { padding: 1rem; }
.ubme-view-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem; }
.ubme-view-tabs { display: flex; gap: 0.25rem; }
.ubme-view-tab { padding: 0.375rem 0.75rem; background: transparent; border: 1px solid transparent; border-radius: 0.375rem; color: #94a3b8; cursor: pointer; font-size: 0.8rem; }
.ubme-view-tab.active { background: #1e293b; border-color: #334155; color: #fff; }
.ubme-view-actions { display: flex; gap: 0.5rem; align-items: center; }
.ubme-search-input { background: #0f172a; border: 1px solid #334155; border-radius: 0.375rem; padding: 0.375rem 0.75rem; color: #fff; font-size: 0.8rem; width: 200px; }
.ubme-create-btn { background: #10b981; color: #fff; border: none; padding: 0.375rem 0.75rem; border-radius: 0.375rem; cursor: pointer; font-size: 0.8rem; }
.ubme-create-btn:hover { background: #059669; }

.ubme-list { display: flex; flex-direction: column; gap: 0.5rem; }
.ubme-list-item { background: #1e293b; border: 1px solid #334155; border-radius: 0.5rem; padding: 0.75rem; cursor: pointer; transition: all 0.15s; }
.ubme-list-item:hover { border-color: #6366f1; }
.ubme-list-item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem; }
.ubme-list-item-name { font-weight: 600; font-size: 0.9rem; }
.ubme-list-item-details { display: flex; flex-wrap: wrap; gap: 0.75rem; font-size: 0.75rem; color: #94a3b8; }
.ubme-list-item-field { }

.ubme-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.ubme-table th { text-align: left; padding: 0.5rem 0.75rem; background: #1e293b; border-bottom: 1px solid #334155; color: #94a3b8; font-weight: 600; }
.ubme-table td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #1e293b; }
.ubme-table-row { cursor: pointer; }
.ubme-table-row:hover { background: #1e293b; }
.ubme-table-name { font-weight: 500; }

.ubme-kanban { display: flex; gap: 1rem; overflow-x: auto; min-height: 400px; }
.ubme-kanban-column { min-width: 280px; background: #0f172a; border-radius: 0.75rem; padding: 0.75rem; }
.ubme-kanban-column-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; font-size: 0.85rem; }
.ubme-kanban-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.ubme-kanban-count { margin-left: auto; background: #1e293b; padding: 0.125rem 0.375rem; border-radius: 999px; font-size: 0.75rem; color: #64748b; }
.ubme-kanban-card { background: #1e293b; border: 1px solid #334155; border-radius: 0.5rem; padding: 0.75rem; margin-bottom: 0.5rem; cursor: pointer; transition: all 0.15s; }
.ubme-kanban-card:hover { border-color: #6366f1; }
.ubme-kanban-card-title { font-weight: 600; font-size: 0.85rem; margin-bottom: 0.375rem; }
.ubme-kanban-card-field { font-size: 0.75rem; color: #94a3b8; }
.ubme-kanban-card-label { color: #64748b; }

.ubme-detail { padding: 1rem; max-width: 800px; margin: 0 auto; }
.ubme-detail-title { margin: 0.5rem 0; font-size: 1.5rem; }
.ubme-detail-meta { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
.ubme-detail-fields { display: flex; flex-direction: column; gap: 1rem; }
.ubme-field { display: flex; flex-direction: column; gap: 0.25rem; }
.ubme-field-readonly { display: flex; flex-direction: column; gap: 0.25rem; }
.ubme-field-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
.ubme-field-value { font-size: 0.9rem; color: #e2e8f0; }
.ubme-input { background: #0f172a; border: 1px solid #334155; border-radius: 0.375rem; padding: 0.5rem 0.75rem; color: #fff; font-size: 0.85rem; }
.ubme-input:focus { outline: none; border-color: #6366f1; }
.ubme-textarea { min-height: 80px; resize: vertical; }
.ubme-select { background: #0f172a; border: 1px solid #334155; border-radius: 0.375rem; padding: 0.5rem 0.75rem; color: #fff; font-size: 0.85rem; }
.ubme-checkbox { width: 18px; height: 18px; accent-color: #6366f1; }
.ubme-empty-state { text-align: center; padding: 3rem 1rem; color: #64748b; }
.ubme-empty-icon { font-size: 3rem; margin-bottom: 1rem; }
.ubme-empty-state h3 { margin: 0 0 0.5rem; color: #94a3b8; }
.ubme-loading { padding: 2rem; text-align: center; color: #64748b; }
.ubme-error { background: #7f1d1d; border: 1px solid #dc2626; padding: 0.5rem; border-radius: 0.375rem; margin: 0.5rem 0; font-size: 0.85rem; }
.ubme-back-btn { background: transparent; border: 1px solid #334155; padding: 0.375rem 0.75rem; border-radius: 0.375rem; color: #94a3b8; cursor: pointer; font-size: 0.8rem; }
.ubme-back-btn:hover { border-color: #6366f1; color: #fff; }
.ubme-status { padding: 0.125rem 0.5rem; border-radius: 999px; font-size: 0.7rem; font-weight: 500; }
.status-active, .status-confirmed, .status-completed, .status-paid, .status-final { background: #064e3b; color: #6ee7b7; }
.status-inactive, .status-cancelled, .status-failed, .status-expired { background: #450a0a; color: #fca5a5; }
.status-pending, .status-inquiry, .status-scheduled, .status-draft, .status-in_progress { background: #422006; color: #fcd34d; }
.status-lead, .status-new, .status-checked_in { background: #0c4a6e; color: #7dd3fc; }

.ubme-workflow-editor { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; }
.ubme-workflow-state-row, .ubme-workflow-transition-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
.ubme-workflow-transition-row span { color: #64748b; }

.ubme-create-form { padding: 1rem; max-width: 600px; margin: 0 auto; }
.ubme-create-form h2 { margin: 0 0 1rem; }
.ubme-create-form .ubme-field { margin-bottom: 0.75rem; }
.ubme-create-form .ubme-form-actions { margin-top: 1.5rem; }

.ubme-discovery { padding: 2rem; max-width: 700px; margin: 0 auto; }
.ubme-discovery-header { text-align: center; margin-bottom: 1.5rem; }
.ubme-discovery-icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }
.ubme-discovery-header h2 { margin: 0 0 0.5rem; }
.ubme-discovery-subtitle { color: #94a3b8; font-size: 0.9rem; margin: 0; }
.ubme-discovery-examples { margin-bottom: 1.5rem; }
.ubme-discovery-examples-label { font-size: 0.8rem; color: #64748b; margin: 0 0 0.5rem; }
.ubme-discovery-example-chips { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.ubme-discovery-chip { background: #1e293b; border: 1px solid #334155; border-radius: 999px; padding: 0.375rem 0.875rem; color: #94a3b8; cursor: pointer; font-size: 0.8rem; transition: all 0.15s; }
.ubme-discovery-chip:hover { border-color: #6366f1; color: #fff; }
.ubme-discovery-form .ubme-form-row { margin-bottom: 1rem; }
.ubme-discovery-form .ubme-btn-primary { width: 100%; padding: 0.75rem; font-size: 1rem; }
.ubme-discovery-generating { text-align: center; padding: 4rem 2rem; }
.ubme-discovery-spinner { font-size: 3rem; }
.ubme-discovery-generating h3 { margin: 1rem 0 0.5rem; }
.ubme-discovery-generating p { color: #94a3b8; font-size: 0.85rem; }
.ubme-discovery-error { text-align: center; padding: 3rem 2rem; }
.ubme-discovery-error-icon { font-size: 3rem; margin-bottom: 1rem; }
.ubme-discovery-error h3 { margin: 0 0 0.5rem; }
.ubme-discovery-preview-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; }
.ubme-discovery-preview-header h2 { margin: 0; }
.ubme-discovery-preview-desc { color: #94a3b8; font-size: 0.85rem; margin: 0 0 1rem; }
.ubme-discovery-badge { background: #064e3b; color: #6ee7b7; padding: 0.125rem 0.5rem; border-radius: 999px; font-size: 0.7rem; }
.ubme-discovery-stats { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.ubme-discovery-stat { flex: 1; background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 0.75rem; text-align: center; }
.ubme-discovery-stat-value { display: block; font-size: 1.5rem; font-weight: 700; }
.ubme-discovery-stat-label { display: block; font-size: 0.7rem; color: #64748b; text-transform: uppercase; }
.ubme-discovery-object-types { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.5rem; }
.ubme-discovery-ot { background: #1e293b; border: 1px solid #334155; border-radius: 0.5rem; padding: 0.75rem; }
.ubme-discovery-ot-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.375rem; }
.ubme-discovery-ot-fields { display: flex; flex-wrap: wrap; gap: 0.25rem; }
.ubme-discovery-actions { display: flex; gap: 0.75rem; justify-content: center; }
`;function g(){if(document.getElementById("ubme-styles"))return;const e=document.createElement("style");e.id="ubme-styles",e.textContent=f,document.head.appendChild(e)}const h={id:"ubme",name:"Universal Business Model Engine",discover:async()=>{g();const e={};try{const r=await p();e.navigation=r,e.hasModules=Object.keys(r).length>0}catch{}try{const r=await c();e.types=r,e.hasTypes=Object.keys(r).length>0}catch{}return e},register:async e=>{const r=e.navigation??{};for(const[o,m]of Object.entries(r)){const t=m;for(const a of t.entries||[]){const i=a.object_type;i&&d.register({id:`ubme_${o}_${i}`,name:`${t.name} - ${a.label}`,description:`View ${a.label}`,supportedObjectTypes:[i],requiredRuntimes:[],layoutTemplate:"list",panels:[]})}}d.register({id:"ubme_builder",name:"Module Builder",description:"Create and manage business modules",supportedObjectTypes:[],requiredRuntimes:[],layoutTemplate:"admin",panels:[]});for(const[o,m]of Object.entries(r)){const t=m;for(const a of t.entries||[]){const i=a.object_type;i&&d.register({id:`ubme_${o}_${i}_workspace`,name:`${t.name} - ${a.label} Workspace`,description:`Full workspace for ${a.label}`,supportedObjectTypes:[i],requiredRuntimes:[],layoutTemplate:"tabs",panels:[]})}}},search:async e=>{var o;const r=[];try{const t=(await(await fetch("/api/ubme/modules",{credentials:"include"})).json()).data||[];for(const a of t)for(const i of a.object_types||[])try{const l=(await(await fetch(`/api/ubme/data/${i.key}`,{credentials:"include"})).json()).data||[];for(const n of l){const s=n.name||((o=n.data)==null?void 0:o.name)||n.id;s.toLowerCase().includes(e.toLowerCase())&&r.push({id:n.id,type:i.name,title:s,subtitle:`${a.name} · ${i.name}`,status:n.status})}}catch{}}catch{}return r},ask:async e=>{try{const o=(await(await fetch("/api/ubme/modules",{credentials:"include"})).json()).data||[];if(o.length===0)return null;let m=`Installed modules: ${o.map(t=>t.name).join(", ")}.`;for(const t of o){const a=(t.object_types||[]).map(i=>`${i.name} (${t.icon||"📦"})`).join(", ");a&&(m+=` ${t.name} has: ${a}.`)}return m}catch{return null}}},w=[{id:"ubme_open_builder",label:"Open Module Builder",icon:"📦",category:"UBME",action:()=>{const e=new CustomEvent("ubme:open-workspace",{detail:{workspaceId:"ubme_builder"}});document.dispatchEvent(e)}},{id:"ubme_new_module",label:"Create New Module",icon:"➕",category:"UBME",action:()=>{const e=new CustomEvent("ubme:open-workspace",{detail:{workspaceId:"ubme_builder",action:"new-module"}});document.dispatchEvent(e)}}];export{w as commandPaletteActions,h as default};
