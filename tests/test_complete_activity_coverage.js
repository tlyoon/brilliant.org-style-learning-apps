"use strict";
// All four interaction modes and MCQs, all three locales, through REAL app/app.js.
// Only synthetic fixtures enter GitHub. Optional exact-hash private package stays local.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const crypto=require("node:crypto");
const path=require("node:path");
const vm=require("node:vm");
const loc=(x)=>({en:x,ms:x+"-ms",zh:x+"-zh"});
const item=(id)=>({id,label:loc(id)});
const modes=[
 {id:"mcq",type:"mcq",answerKey:{options:[item("a"),item("b")],correct:"b"}},
 {id:"sel",type:"interactive",interactionMode:"selection",
  interaction:{items:[item("a"),item("b"),item("c")],correctSelections:["a","c"]}},
 {id:"match",type:"interactive",interactionMode:"matching",
  interaction:{items:[item("a"),item("b")],targets:[item("x"),item("y")],
               placements:[{itemId:"a",targetId:"y"},{itemId:"b",targetId:"x"}]}},
 {id:"class",type:"interactive",interactionMode:"classification",
  interaction:{items:[item("a"),item("b")],targets:[item("x"),item("y")],
               placements:[{itemId:"a",targetId:"x"},{itemId:"b",targetId:"y"}]}},
 {id:"order",type:"interactive",interactionMode:"ordering",
  interaction:{items:[item("a"),item("b"),item("c")],correctOrder:["a","b","c"]}},
].map(x=>({...x,prompt:loc("prompt"),hints:[loc("hint")],feedback:loc("feedback"),difficulty:"medium"}));
function getPackage(){
 const file=process.env.BRILLIANT_PRIVATE_PACKAGE;
 const expected=process.env.BRILLIANT_EXPECTED_SHA256;
 if(!file&&!expected)return {subchapter:loc("test"),activities:modes};
 assert(file&&expected&&path.isAbsolute(file),"private source requires an absolute path and SHA");
 const root=path.resolve(".");
 const canonical=path.resolve(file);
 assert(!canonical.startsWith(root+path.sep),"never load private source from Git");
 const raw=fs.readFileSync(canonical);
 assert.equal(crypto.createHash("sha256").update(raw).digest("hex"),expected.toLowerCase());
 const data=JSON.parse(raw.toString("utf8"));
 assert.equal(data.activities.length,18,"actual Section 9.4 contract requires 18");
 return data;
}
class Element{
 constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.attributes={};
 this.dataset={};this.style={};this.listeners={};this.className="";this.disabled=false;this._text="";}
 set innerHTML(_){throw new Error("unsafe HTML");}
 set textContent(v){this._text=String(v);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>c.textContent).join("");}
 append(...xs){this.children.push(...xs);}
 replaceChildren(...xs){this._text="";this.children=[...xs];}
 setAttribute(k,v){this.attributes[k]=String(v);if(k==="id")this.id=String(v);}
 addEventListener(k,f){this.listeners[k]=f;}
 focus(){this.focused=true;}
 click(){if(!this.disabled)this.listeners.click?.({target:this});}
}
const nodes=(root)=>[root,...root.children.flatMap(nodes)];
const find=(root,fn)=>nodes(root).find(fn);
const matching=(root,fn)=>nodes(root).filter(fn);
async function exercise(activity,lang){
 const root=new Element("section");root.dataset.packageUrl="fixture";
 const locale=new Element("select");
 const doc={
  createElement:t=>new Element(t),
  querySelector:s=>s==="#app"?root:locale,
  querySelectorAll:s=> {
   const classes={"#app .target-choice":"choice target-choice","#app .choices button":"choice",
                  "#app .order-control":"secondary order-control"};
   return matching(root,e=>e.className===classes[s]);
  },
 };
 const sandbox={document:doc,console,fetch:async()=>({ok:true,json:async()=>
   ({subchapter:loc("test"),activities:[activity]})})};
 vm.runInNewContext(fs.readFileSync("app/app.js","utf8"),sandbox,{filename:"app/app.js"});
 await new Promise(resolve=>setImmediate(resolve));
 locale.value=lang;
 locale.listeners.change({target:locale});
 assert.equal(find(root,x=>x.className==="question").textContent,
              activity.prompt[lang],"prompt translation not displayed");
 const hint=activity.hints?.[0]?.[lang];
 assert(typeof hint==="string"&&hint.trim(),"localized hint missing");
 find(root,x=>x.id==="hint").click();
 assert(matching(root,x=>x.className==="feedback").some(x=>x.textContent===hint));
 const choose=(id)=>{const c=find(root,x=>x.tagName==="BUTTON"&&x.dataset.value===id);
   assert(c,"option missing");c.click();};
 if(activity.type==="mcq"){
   const wrong=activity.answerKey.options.find(x=>x.id!==activity.answerKey.correct);
   if(wrong){
      choose(wrong.id);find(root,x=>x.id==="check").click();
      assert(matching(root,x=>x.className==="feedback").at(-1).textContent.includes(activity.feedback[lang]));
      find(root,x=>x.id==="check").click();
   }
   choose(activity.answerKey.correct);
 } else if(activity.interactionMode==="selection"){
   for(const id of activity.interaction.correctSelections)choose(id);
 }else if(["matching","classification"].includes(activity.interactionMode)){
   for(const placement of activity.interaction.placements){
     const control=find(root,x=>x.className==="choice target-choice"&&
       x.dataset.itemId===placement.itemId&&x.dataset.targetId===placement.targetId);
     assert(control,"missing keyed placement");control.click();
     assert(control.focused || matching(root,x=>x.className==="choice target-choice").some(x=>x.focused),
       "target focus not restored");
   }
 }else if(activity.interactionMode==="ordering"){
   const target=activity.interaction.correctOrder;
   for(let index=0;index<target.length;index++){
      for(let attempts=0;attempts<target.length;attempts++){
        const rows=matching(root,x=>x.className==="order-row");
        const at=rows.findIndex(x=>x.dataset.itemId===target[index]);
        if(at===index)break;
        assert(at>index,"unexpected order");
        const up=find(rows[at],x=>x.className==="secondary order-control"&&x.dataset.delta==="-1");
        assert(up&&!up.disabled,"ordering up control missing");up.click();
      }
   }
 }else throw new Error("unrecognized interaction mode");
 const check=find(root,x=>x.id==="check");
 assert(check&&!check.disabled, "response not complete");
 check.click();
 const last=matching(root,x=>x.className==="feedback").at(-1);
 assert(last.textContent.includes(activity.feedback[lang]),"localized feedback missing");
 const advance=find(root,x=>x.id==="check");
 assert(advance.textContent.trim(),"success button missing");
 advance.click();
 assert(find(root,x=>x.id==="restart"),"activity did not finish correctly");
}
(async()=>{
 const pkg=getPackage();
 const counts={mcq:0,classification:0,matching:0,ordering:0,selection:0};
 for(const activity of pkg.activities){
   if(activity.type==="mcq")counts.mcq++;
   else counts[activity.interactionMode]=(counts[activity.interactionMode]||0)+1;
   for(const lang of ["en","ms","zh"])await exercise(activity,lang);
 }
 if(process.env.BRILLIANT_PRIVATE_PACKAGE){
   assert.equal(counts.mcq,9);
   assert.equal(Object.values(counts).reduce((a,b)=>a+b,0),18);
 }
 console.log(JSON.stringify({privateOriginal:!!process.env.BRILLIANT_PRIVATE_PACKAGE,
  activities:pkg.activities.length,locales:3,journeys:pkg.activities.length*3,modes:counts,
  academicQA:"REVIEW_REQUIRED",publicationAuthorized:false}));
})().catch(err=>{
 console.error("Player coverage blocked",err.name,
   process.env.BRILLIANT_PRIVATE_PACKAGE?"":"in fixture");
 process.exitCode=1;
});