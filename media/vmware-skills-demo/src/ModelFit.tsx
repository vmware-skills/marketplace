import React from 'react';

type Lang = 'en' | 'zh';
const tx = (lang: Lang, en: string, zh: string) => lang === 'en' ? en : zh;

export const ModelFit: React.FC<{lang: Lang; progress: number}> = ({lang, progress}) => {
  const active = Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const steps = [
    [tx(lang, 'Connect', '连接模型'), tx(lang, 'Record size, quantization and context.', '记录尺寸、量化和上下文。')],
    [tx(lang, 'Test', '统一测试'), tx(lang, '10 final tasks × 5 attempts. Same sealed cases.', '10 道保留题 × 5 次，使用同一封存题集。')],
    [tx(lang, 'Review', '质量复核'), tx(lang, 'Schema checks + human answer and safety review.', '结构自动检查，加人工答案与安全复核。')],
    [tx(lang, 'Compare', '分组选择'), tx(lang, 'Smallest tested passing configuration per task group.', '选择该组已测通过的合适配置。')],
  ];
  return <div style={{background:'white',border:'1px solid #dce5ef',borderRadius:22,padding:32}}>
    <div style={{fontSize:25,color:'#0891b2',fontWeight:700,marginBottom:25}}>marketplace / model-fit</div>
    <div style={{display:'grid',gridTemplateColumns:'repeat(4, 1fr)',gap:16}}>
      {steps.map(([title, body], index) => <div key={index} style={{borderRadius:16,padding:22,minHeight:215,boxSizing:'border-box',background:index===active?'#e7f7fb':'#f5f8fc',border:`2px solid ${index===active?'#0891b2':'#dce5ef'}`}}>
        <div style={{fontSize:21,color:'#64748b',marginBottom:12}}>0{index+1}</div>
        <div style={{fontSize:32,fontWeight:750,marginBottom:16}}>{title}</div>
        <div style={{fontSize:25,lineHeight:1.4}}>{body}</div>
      </div>)}
    </div>
    <div style={{fontSize:25,fontWeight:650,marginTop:24}}>{tx(lang, 'Supporting capability: assess model fit for your team’s tasks.', '辅助能力：验证模型是否适合团队的任务。')}</div>
    <div style={{fontSize:22,lineHeight:1.45,color:'#a45b08',marginTop:12}}>{tx(lang, 'Synthetic tasks only · No VMware calls · No real model scores yet', '仅合成任务 · 不执行 VMware 调用 · 暂无真实模型成绩')}</div>
  </div>;
};
