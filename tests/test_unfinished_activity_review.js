"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
class E{
 constructor(t){this.tagName=t.toUpperCase();this.children=[];this.attributes={};
 this.dataset={};this.style={};this.listeners={};this.className="";this.disabled=false;this._text="";}
 set innerHTML(v){throw Error("untrusted html");}
 set textContent(x){this._text=String(x);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>x.textContent).join("");}
 append(...a){this.children.push(...a);}
 replaceChildren(...a){this._text="";this.children=[...a];}
 setAttribute(k,v){this.attributes[k]=String(v);if(k==="id")this.id=String(v);}
 addEventListener(k,f){this.listeners[k]=f;}
 focus(){this.focused=true;}
 click(){if(!this.disabled)this.listeners.click?.({target:this});}
}
const all=e=>[e,...e.children.flatMap(all)];
const loc=x=>({en:x,ms:x,zh:x});
const p={subchapter:loc("learning"),activities:[
 {id:"first",type:"mcq",difficulty:"easy",prompt:loc("first"),feedback:loc("why"),
  hints:[loc("hint")],answerKey:{options:[{id:"wrong",label:loc("no")},
    {id:"right",label:loc("yes")}],correct:"right"}},
 {id:"second",type:"mcq",difficulty:"medium",prompt:loc("second"),feedback:loc("why"),
  hints:[loc("hint")],answerKey:{options:[{id:"wrong",label:loc("no")},
    {id:"right",label:loc("yes")}],correct:"right"}},
]};
const app=new E("section");app.dataset.packageUrl="synthetic";
const locale=new E("select");
const ctx={console,document:{
 createElement:t=>new E(t),
 querySelector:s=>s==="#app"?app:locale,
 querySelectorAll:s=>s==="#app .choices button"?all(app).filter(e=>e.className==="choice"):[],
},fetch:async()=>({ok:true,json:async()=>p})};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync("app/app.js","utf8"),ctx);
const button=id=>all(app).find(e=>e.id===id);
const choice=id=>all(app).find(e=>e.dataset?.value===id);
const metrics=()=>JSON.parse(vm.runInContext("JSON.stringify(state.sessionMetrics)",ctx));
setImmediate(()=>{
 button("skip").click();
 assert.equal(metrics().first.skips,1);
 assert.equal(metrics().first.completed,false);
 choice("right").click();button("check").click();button("check").click();
 assert(button("restart"));
 let progress=all(app).find(e=>e.className==="progress-summary");
 assert(progress.textContent.includes("1 / 2"),"skip must not count as correctly completed");
 locale.value="ms";locale.listeners.change({target:locale});
 progress=all(app).find(e=>e.className==="progress-summary");
 assert(progress.textContent.includes("Diselesaikan dengan betul"));
 assert(button("review-pending"),"must offer revisit of unfinished activity");
 button("review-pending").click();
 assert(all(app).find(e=>e.className==="question").textContent==="first");
 choice("right").click();button("check").click();button("check").click();
 assert(button("restart"),"review queue should return to completion");
 progress=all(app).find(e=>e.className==="progress-summary");
 assert(progress.textContent.includes("2 / 2"));
 assert.equal(button("review-pending"),undefined,"no incomplete activities remain");
 assert.equal(metrics().first.completed,true);
 assert.equal(metrics().second.completed,true);
 button("restart").click();
 assert.deepEqual(metrics(),{});
 console.log("Skipped activity revisited and completed; completion not falsely awarded.");
});
