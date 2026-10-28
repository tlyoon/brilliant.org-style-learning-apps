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
const loc=x=>({en:x,ms:x+'-ms',zh:x+'-zh'});
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
 choice("wrong").click();
 button("check").click();
 assert.equal(metrics().first.wrong,1);
 assert.equal(metrics().first.hints,0);
 assert.equal(all(app).some(e=>e.className==="feedback"&&e.textContent==="hint"),false,
  "one wrong attempt cannot auto-reveal hint");
 button("check").click();
 locale.value="ms";locale.listeners.change({target:locale});
 choice("wrong").click();
 button("check").click();
 assert.equal(metrics().first.wrong,2);
 assert.equal(metrics().first.autoHintShown,true);
 assert.equal(metrics().first.hints,1);
 assert(all(app).some(e=>e.className==="feedback"&&e.textContent==="hint-ms"),
   "two incorrect checks should reveal authored Malay hint");
 locale.value="zh";locale.listeners.change({target:locale});
 assert(all(app).some(e=>e.className==="feedback"&&e.textContent==="hint-zh"),
   "automatic hint must follow current locale");
 button("check").click();
 choice("right").click();
 button("check").click();
 assert.equal(metrics().first.correct,1,"hint does not invalidate correct grading");
 assert.equal(metrics().first.hints,1,"auto hint counted only once");
 button("check").click();
 assert(metrics().first.completed);
 console.log("Repeated misconceptions reveal only localized authored hint; grading unchanged.");
});
