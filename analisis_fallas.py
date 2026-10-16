"""Preguntas 6-11. Ejecutar después de pipeline.py y analisis_enlace.py."""
from pathlib import Path
import json, sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path(__file__).resolve().parent
OUT=BASE/'resultados'
JOIN_SQL='''SELECT a.id,a.ts,a.seq,b.id AS id_original,b.ts AS ts_original
FROM tramas a JOIN tramas b
ON a.seq=b.seq AND a.t_ms=b.t_ms AND a.t_mcu=b.t_mcu
AND a.a0=b.a0 AND a.pulsos=b.pulsos AND a.boton=b.boton
AND b.id<a.id ORDER BY a.id;'''
def main():
    d=pd.read_csv(OUT/'tramas_analisis.csv');d.ts=pd.to_datetime(d.ts)
    with sqlite3.connect(BASE/'cps_lab3.db') as con:
        j=pd.read_sql_query(JOIN_SQL,con)
        rejects=pd.read_sql_query('SELECT * FROM rechazos ORDER BY id',con)
    j['minuto']=(pd.to_datetime(j.ts)-pd.Timestamp('2026-10-08 15:00')).dt.total_seconds()/60
    replay=j[j.minuto.between(22,24)]
    failures=[]
    for i in d.index[(d.seq==1)&(d.dt>10)]:
        prev,now=d.loc[i-1],d.loc[i]
        garbage=rejects[(rejects.causa=='basura')&(pd.to_datetime(rejects.ts)>prev.ts)&(pd.to_datetime(rejects.ts)<now.ts)]
        assert now.t_ms<prev.t_ms and len(garbage)>0
        failures.append({'previa':str(prev.ts),'posterior':str(now.ts),'reparacion_s':now['dt']})
    f=pd.DataFrame(failures);total=f.reparacion_s.sum()
    m=json.loads((OUT/'metricas_enlace.json').read_text())
    mttr=total/len(f);mtbf=(m['T_s']-total)/len(f)
    # Detector retrospectivo: 3 o más saltos >20 en 5 diferencias centradas.
    d['flotante']=(d.a0.diff().abs()>20).rolling(5,center=True,min_periods=5).sum()>=3
    n=1.22*d.t_mcu+324.31
    d['residuo_adc']=(n-n.round()).abs();d['fdi_adc']=d.residuo_adc>.07
    outside=~(d.minuto.between(13,17)|d.minuto.between(22,24))
    d['tasa_C_s']=d.t_mcu.diff().abs()/d.dt
    baseline=outside&outside.shift(fill_value=False)
    maximum=d.loc[baseline,'tasa_C_s'].max();threshold=.42
    assert threshold>maximum
    d['alarma_tasa']=d.tasa_C_s>threshold
    for name,frame in [('desconexiones',f),('coincidencias_join',j),('replay',replay),('deteccion_flotante',d[d.flotante]),('deteccion_adc',d[d.fdi_adc]),('deteccion_tasa',d[d.alarma_tasa]),('analisis_completo',d)]:
        frame.to_csv(OUT/(name+'.csv'),index=False)
    pre=d[d.minuto.between(13,14.2)].t_mcu.mean();post=d[d.minuto.between(15.8,17)].t_mcu.mean()
    stats={'MTTR_s':mttr,'MTBF_s':mtbf,'A_porcentaje':100*mtbf/(mtbf+mttr),'reparacion_total_s':total,'flotante_marcadas':int(d.flotante.sum()),'fdi_tramas':int(d.fdi_adc.sum()),'temperatura_pre':pre,'temperatura_post':post,'temperatura_fdi':d.loc[d.fdi_adc,'t_mcu'].mean(),'alteracion_media_C':d.loc[d.fdi_adc,'t_mcu'].mean()-(pre+post)/2,'max_tasa_referencia':maximum,'umbral_tasa':threshold,'alarmas_tasa':int(d.alarma_tasa.sum()),'replay_tramas':len(replay),'D_corregida':100*(m['Nval']-len(replay))/m['Nesp'],'L_autenticada':m['L_bytes']+34,'rho_autenticada':100*10*(m['L_bytes']+34)*m['X_tramas_s']/115200}
    (OUT/'metricas_fallas.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
    plt.rcParams.update({'font.size':10})
    fig,ax=plt.subplots(figsize=(10,3.8),layout='constrained');ax.plot(d.minuto,d.a0,'.-',ms=2,lw=.6);ax.scatter(d.loc[d.flotante,'minuto'],d.loc[d.flotante,'a0'],s=15,color='#c44b37',label='Detector de fluctuaciones');ax.set(xlabel='Minuto de captura',ylabel='A0 [cuentas ADC]',title='Potenciómetro: giros y entrada flotante');ax.legend();ax.grid(alpha=.2);fig.savefig(OUT/'sensor_a0.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(2,1,figsize=(10,5),sharex=True,layout='constrained');w=d[d.minuto.between(13,17)];axs[0].plot(w.minuto,w.t_mcu,'.-',ms=3);axs[0].set(ylabel='Temperatura [°C]',title='Inyección de datos falsos');axs[1].plot(w.minuto,w.residuo_adc,'.-');axs[1].axhline(.07,color='red',ls='--',label='Tolerancia 0,07');axs[1].set(xlabel='Minuto de captura',ylabel='Distancia al entero');axs[1].legend();fig.savefig(OUT/'fdi.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,3.4),layout='constrained');w=d[d.minuto.between(22,24)];ax.plot(w.minuto,w.seq,'.-');ax.axvspan(replay.minuto.min(),replay.minuto.max(),color='#d98259',alpha=.25);ax.set(xlabel='Minuto de captura',ylabel='seq',title='Replay: retroceso sin reinicio ni interrupción del flujo');fig.savefig(OUT/'replay.png',dpi=160);plt.close(fig)
    print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
