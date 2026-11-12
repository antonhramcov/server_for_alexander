import {readFileSync} from 'node:fs';
import {createConfig,validateCopy} from './content.js';
const read=path=>JSON.parse(readFileSync(new URL('../content/'+path,import.meta.url),'utf8'));
export const MANIFEST=read('catalog.json');
export const COPY=validateCopy(read(MANIFEST.interfaceFile));
export const DOCUMENTS=MANIFEST.standards.filter(s=>s.status==='ready').map(s=>read(s.file));
export const CONFIGS=DOCUMENTS.map(doc=>createConfig(doc,COPY));
export const CONFIG=CONFIGS[0];
export const WELCOME={title:COPY.welcome.heading,intro:COPY.welcome.description,sections:COPY.stages.sections,seo:COPY.seo};
export function loadEdition(){return {manifest:MANIFEST,copy:COPY,documents:DOCUMENTS,configs:CONFIGS};}
