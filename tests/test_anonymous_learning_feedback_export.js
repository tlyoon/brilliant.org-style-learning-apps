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
let capture=null;
const originalClick=E.prototype.click;
E.prototype.click=function(){
  if(this.tagName==="A"){capture={...this.attributes};return;}
  return originalClick.call(this);
};
p.activities[0].prompt=loc("private-source-question-content");
p.activities[1].feedback=loc("private-scientific-feedback-content");
setImmediate(()=>{
 assert.equal(capture,null,"no export before learner opt in");
 button("skip").click();
 choice("wrong").click();button("check").click();button("check").click();
 choice("right").click();button("check").click();button("check").click();
 assert(button("export-feedback"),"export option missing at completion");
 assert.equal(capture,null,"no automatic data download");
 button("export-feedback").click();
 assert(capture&&capture.download==="anonymous-learning-feedback.json");
 assert(capture.href.startsWith("data:application/json;charset=utf-8,"));
 const report=JSON.parse(decodeURIComponent(capture.href.split(",").slice(1).join(",")));
 assert.equal(report.schemaVersion,1);
 assert.equal(report.activitiesTotal,2);
 assert.equal(report.containsStudentIdentity,false);
 assert.equal(report.publicationAuthorized,false);
 assert.deepEqual(report.activities.map(x=>x.activityId),["first","second"]);
 assert.equal(report.activities[0].skips,1);
 assert.equal(report.activities[0].completed,false);
 assert.equal(report.activities[1].wrong,1);
 assert.equal(report.activities[1].correct,1);
 assert.equal(report.activities[1].completed,true);
 assert(!JSON.stringify(report).includes("private-source-question-content"));
 assert(!JSON.stringify(report).includes("private-scientific-feedback-content"));
 assert(!("username" in report)&&!("timestamp" in report));
 console.log("Anonymous opt-in feedback JSON contains only activity IDs and outcome counts.");
});
