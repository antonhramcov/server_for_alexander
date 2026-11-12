// Development/test catalog; production uses lazy content loading in hosted.js.
import {CONFIGS,MANIFEST} from './config.js';
export {selectableStandard,validateConfig} from './validation.js';
export const STANDARDS=MANIFEST.standards.map(item=>({...item,config:CONFIGS.find(c=>c.id===item.id)}));
