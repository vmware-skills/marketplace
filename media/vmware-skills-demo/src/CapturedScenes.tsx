import React from 'react';
import {Freeze, OffthreadVideo, staticFile} from 'remotion';
type Lang='en'|'zh';
const t=(l:Lang,en:string,zh:string)=>l==='en'?en:zh;
const panel:React.CSSProperties={background:'#fff',border:'1px solid #dce5ef',borderRadius:22,padding:24};
// Native RGB capture frames are lossless. Integer scaling preserves the source glyph edges.
const Excerpt:React.FC<{name:string;style?:React.CSSProperties}>=({name,style})=><Freeze frame={0}><OffthreadVideo muted src={staticFile(`captures/${name}.mp4`)} style={{display:'block',imageRendering:'pixelated',...style}}/></Freeze>;
const Label:React.FC<{children:React.ReactNode}>=({children})=><div style={{fontSize:23,fontWeight:700,color:'#0891b2',marginBottom:18}}>{children}</div>;
export const RecordedInventory:React.FC<{lang:Lang}>=({lang})=><div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:28}}>
 <div style={{...panel,minHeight:440}}><Label>{t(lang,'Historical screenshot excerpt','中文历史截图节选')}</Label>{lang==='en'?<Excerpt name="en-inventory" style={{width:603,height:400.5,margin:'0 auto'}}/>:<>
  <div style={{fontSize:28,marginBottom:18}}>场景：查询虚拟机清单</div>
  <Excerpt name="zh-question" style={{width:620,height:27,margin:'0 auto 35px'}}/>
  <Excerpt name="zh-inventory" style={{width:660,height:28,margin:'0 auto 30px'}}/>
  <div style={{fontSize:23,lineHeight:1.7,color:'#64748b'}}>保留中文会话里的原始返回。<br/>主机地址和虚拟机名称未展示。</div>
 </>}</div>
 <div style={{...panel}}><Label>{t(lang,'Readable transcript · selected values','大字转录 · 所选数值')}</Label><div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:14,margin:'30px 0'}}>{[['13',t(lang,'VMs returned','虚拟机')],['6',t(lang,'Powered on','运行中')],['7',t(lang,'Powered off','已关机')]].map(([n,label])=><div key={label} style={{padding:'30px 18px',background:'#e7f7fb',borderRadius:15}}><div style={{fontSize:64,fontWeight:750,color:'#0891b2'}}>{n}</div><div style={{fontSize:28,marginTop:18}}>{label}</div></div>)}</div>
 <div style={{fontSize:28,lineHeight:1.65}}>{t(lang,'Recorded query scope. Verify today’s inventory separately.','这是当时查询范围内的结果。当前环境需重新查询核对。')}</div>
 </div>
</div>;
export const RecordedHealth:React.FC<{lang:Lang}>=({lang})=><div style={panel}>
 <Label>{t(lang,'Historical health summary · original screenshot','中文历史健康报告 · 原图节选')}</Label>
 <div style={{height:lang==='zh'?290:144,display:'flex',justifyContent:'center',alignItems:'center'}}><Excerpt name={`${lang}-health`} style={lang==='zh'?{width:1064,height:290}:{width:1364,height:144}}/></div>
 <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:20,marginTop:18}}>{[
 [t(lang,'CONNECTED HOSTS','已连接主机'),'2 / 2'],
 [t(lang,'RECORDED CRITICAL ALARMS','报告中的严重告警'),'2'],
 [t(lang,'NEXT CHECK','下一步'),t(lang,'Recheck current state','重新核对当前状态')]
 ].map(([label,value])=><div key={label} style={{padding:14,background:'#e7f7fb',borderRadius:14,display:'flex',alignItems:'center',justifyContent:'space-between',gap:15}}><div style={{fontSize:19,color:'#0891b2',fontWeight:700}}>{label}</div><div style={{fontSize:28,fontWeight:650}}>{value}</div></div>)}</div>
 <div style={{fontSize:18,color:'#64748b',marginTop:10}}>{t(lang,'Readable transcript below the original · historical alarms require a fresh check','原图下方为大字转录 · 历史告警不代表当前仍有故障')}</div>
</div>;
const englishAudit=[
 ['1','13:10:24','monitor','list_all_clusters','MCP','277 ms'],
 ['2','13:10:25','monitor','list_esxi_hosts','MCP','226 ms'],
 ['3','13:10:25','monitor','list_all_datastores','MCP','102 ms'],
 ['4','13:10:26','monitor','list_all_networks','MCP','249 ms'],
 ['5','13:10:26','monitor','list_virtual_machines','MCP','523 ms'],
 ['6','13:11:36','monitor','cluster_health_summary','MCP','465 ms'],
 ['7','13:11:37','monitor','host_performance','MCP','383 ms'],
 ['8','13:11:37','monitor','datastore_capacity','MCP','195 ms'],
 ['9','13:11:37','monitor','get_alarms','MCP','217 ms'],
 ['10','13:13:44','aiops','get_cluster_health_summary (summary --html)','CLI','1,248 ms'],
 ['11','13:14:25','aria','get_aria_health','MCP','696 ms'],
 ['12','13:14:25','aria','list_resources (clusters)','MCP','118 ms'],
 ['13','13:14:25','aria','list_resources (hosts)','MCP','33 ms'],
 ['14','13:14:25','aria','list_alerts (Critical)','MCP','162 ms']
];
const chineseAudit=[
 ['34181','20:33:56','aiops','doctor'],['34182','20:37:15','monitor','list_virtual_machines'],['34183','20:37:16','monitor','list_esxi_hosts'],['34184','20:37:17','monitor','list_virtual_machines'],['34185','20:37:18','monitor','list_esxi_hosts'],
 ['34191','20:41:40','monitor','get_cluster_health_summary'],['34192','20:42:58','monitor','get_datastore_capacity'],['34193','20:43:00','monitor','get_datastore_capacity'],['34194','21:36:19','harden','scan_target'],['34195','21:40:39','aria','doctor'],
 ['34196','21:41:09','aria','list_resources'],['34197','21:41:10','aria','list_resources'],['34198','21:41:10','aria','get_aria_node_resources'],['34199','21:41:10','aria','list_adapters'],['34200','21:41:10','aria','list_alerts']
];
export const RecordedAudit:React.FC<{lang:Lang;progress:number}>=({lang,progress})=>{
 const rows=lang==='en'?englishAudit:chineseAudit;const index=Math.min(rows.length-1,Math.floor(progress*rows.length));const page=Math.floor(index/5);const row=rows[index];
 return <div style={{...panel,padding:20}}>
  <div style={{display:'flex',justifyContent:'space-between',marginBottom:10,fontSize:23,fontWeight:700,color:'#0891b2'}}><span>{t(lang,'Screenshot · assistant-prepared audit export view','中文截图 · 助手整理的审计记录')}</span><span style={{fontSize:22,color:'#64748b'}}>{t(lang,'Excerpt page','节选分屏')} {page+1} / 3</span></div>
  <div style={{height:336,display:'flex',justifyContent:'center',alignItems:'center',overflow:'hidden'}}><Excerpt name={`${lang}-audit-${page}`} style={{width:lang==='en'?1328:1116,height:'auto'}}/></div>
  <div style={{background:'#e7f7fb',padding:'12px 24px',borderRadius:12,marginTop:12}}>
   <div style={{fontSize:20,color:'#0891b2',fontWeight:700,marginBottom:7}}>{t(lang,'READABLE TRANSCRIPT · SELECTED ROW','大字转录 · 当前选中记录')} #{row[0]} · {row[1]} · {row[2]} · {lang==='en'?`${row[4]} · ok · ${row[5]}`:'ok'}</div>
   <div style={{fontSize:29,fontFamily:'monospace',fontWeight:650}}>{row[3]}</div>
  </div>
  <div style={{fontSize:18,color:'#64748b',marginTop:10}}>{t(lang,'Targets omitted · recorded-version names · excerpt, not a completeness proof','已省略目标列 · 保留当时工具名 · 节选不构成完整性证明')}</div>
 </div>;
};
