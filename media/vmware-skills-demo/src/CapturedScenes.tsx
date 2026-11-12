import React from 'react';
import {Freeze, OffthreadVideo, staticFile} from 'remotion';
type Lang='en'|'zh';
const t=(l:Lang,en:string,zh:string)=>l==='en'?en:zh;
const panel:React.CSSProperties={background:'#fff',border:'1px solid #dce5ef',borderRadius:22,padding:28};
const Excerpt:React.FC<{name:string;style?:React.CSSProperties}>=({name,style})=><Freeze frame={0}><OffthreadVideo muted src={staticFile(`captures/${name}.mp4`)} style={{display:'block',width:'100%',...style}}/></Freeze>;
export const RecordedInventory:React.FC<{lang:Lang}>=({lang})=><div style={{display:'grid',gridTemplateColumns:'0.9fr 1.1fr',gap:28}}>
 <div style={{...panel,padding:22}}><div style={{fontSize:22,fontWeight:700,color:'#0891b2',marginBottom:15}}>{t(lang,'Original inventory table excerpt','原始清单表格节选')}</div><Excerpt name="inventory" style={{maxHeight:410,objectFit:'contain'}}/></div>
 <div style={{padding:'15px 10px'}}><div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:16}}>{[['1','vCenter'],['2',t(lang,'ESXi hosts','ESXi 主机')],['13',t(lang,'VMs returned','返回的 VM')]].map(([n,label])=><div key={label} style={{...panel,padding:22}}><div style={{fontSize:58,fontWeight:750,color:'#0891b2'}}>{n}</div><div style={{fontSize:23,color:'#64748b'}}>{label}</div></div>)}</div>
 <div style={{fontSize:29,lineHeight:1.75,marginTop:28}}>{t(lang,'Standalone hosts; no cluster returned.','独立主机；未返回集群。')}<br/>{t(lang,'6 VMs powered on, 7 powered off.','6 台开机，7 台关机。')}</div>
 <div style={{fontSize:23,lineHeight:1.6,color:'#64748b',marginTop:25}}>{t(lang,'Historical query scope, not a new live inventory. The notes column is omitted to protect environment identifiers.','历史查询范围，不是当前环境的新清单。已裁去含环境标识的备注列。')}</div></div>
</div>;
export const RecordedHealth:React.FC<{lang:Lang}>=({lang})=><div>
 <div style={{...panel}}><div style={{fontSize:23,fontWeight:700,color:'#0891b2',marginBottom:20}}>{t(lang,'Captured health summary · original values retained','历史健康摘要 · 保留原始数值')}</div><Excerpt name="health" style={{width:'100%',maxHeight:200,objectFit:'contain'}}/></div>
 <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:18,marginTop:22}}>{[
 [t(lang,'OBSERVED','已观测'),t(lang,'Two hosts connected.','两台主机已连接。')],
 [t(lang,'RECORDED','已记录'),t(lang,'Critical alarms in this snapshot.','该快照中存在严重告警。')],
 [t(lang,'NEXT CHECK','下一步'),t(lang,'Recheck alarm age and current state.','复核告警时效与当前状态。')]
 ].map(([label,text],i)=><div key={label} style={{...panel,padding:24}}><div style={{fontSize:20,fontWeight:700,color:i===1?'#d97706':'#0891b2',marginBottom:15}}>{label}</div><div style={{fontSize:27,lineHeight:1.45}}>{text}</div></div>)}</div>
</div>;
export const RecordedAudit:React.FC<{lang:Lang;progress:number}>=({lang,progress})=>{
 const lower=progress>=.5;
 return <div style={{...panel,padding:24}}>
  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:18}}><span style={{fontSize:24,fontWeight:700,color:'#0891b2'}}>{t(lang,'Exported audit records → assistant-prepared view','审计导出记录 → 助手整理的会话视图')}</span><span style={{fontSize:23,color:'#64748b'}}>{lower?t(lang,'Excerpt: rows 8–14','节选：第 8–14 行'):t(lang,'Excerpt: rows 1–7','节选：第 1–7 行')}</span></div>
  <Excerpt name={lower?'audit-bottom':'audit-top'} style={{width:1127,height:360,objectFit:'contain',margin:'0 auto'}}/>
  <div style={{fontSize:21,lineHeight:1.45,color:'#64748b',marginTop:12}}>{t(lang,'Target column omitted · captured tool names may differ from current releases · not a completeness proof','已省略目标列 · 工具名为截图当时版本，可能与当前版本不同 · 不构成完整性证明')}</div>
 </div>;
};
