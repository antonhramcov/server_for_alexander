import {CONFIGS,MANIFEST} from './src/config.js';
const ids=new Set();
for(const item of MANIFEST.standards){
 if(ids.has(item.id)||item.status!=='ready'||item.file!=='standards/'+item.id+'.json'||!CONFIGS.some(c=>c.id===item.id))throw new Error('Invalid catalog entry: '+item.id);
 ids.add(item.id);
}
console.log(`Validated: ${CONFIGS.length} standards, ${CONFIGS.reduce((n,c)=>n+c.questions.length,0)} questions.`);
