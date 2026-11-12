"""Offline CLI process tests through native OMP; no credentials or inference.

Run: python3 -m unittest discover -s tests -p test_omp_cli.py -v
Requires OMP 18.14.0 (OMP_CLI_TEST_OMP overrides discovery) and Python 3.
Missing OMP skips; loader/runtime failures fail. Fake CLI runs in isolated HOME.
Managed-policy hooks remain authorized; fake tests do not prove hook suppression.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]

FAKE = r'''
import json, os, pathlib, subprocess, sys, time
home = pathlib.Path.home()
config = json.loads((home / "case.json").read_text())
(home / "pid").write_text(str(os.getpid()))
payload = sys.stdin.read()
(home / "capture.json").write_text(json.dumps({"argv":sys.argv[1:],"input":payload,"env":dict(os.environ)}))
mode = config.get("mode","ok")
if mode in ("group", "escaped"):
    child = subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"],start_new_session=mode=="escaped")
    (home / "grandchild").write_text(str(child.pid))
if mode in ("hang", "group", "escaped"):
    while True: time.sleep(1)
if mode == "exit": sys.exit(7)
if mode == "invalid":
    print("not json")
    sys.exit()
if mode in ("overflow", "stderr"):
    stream = sys.stderr if mode=="stderr" else sys.stdout
    stream.write("x"*100000)
    stream.flush()
    while True: time.sleep(1)
print(json.dumps({"type":"result","subtype":"success","is_error":False,
    "structured_output":config.get("result",{"text":"answer","toolCalls":[]}),
    "usage":{"input_tokens":11,"output_tokens":7,"cache_read_input_tokens":3,"cache_creation_input_tokens":2},
    "total_cost_usd":config.get("cost",0),**config.get("envelope",{})}))
'''

HARNESS = r'''
import assert from "node:assert/strict";
import { readFileSync, writeFileSync, existsSync, unlinkSync, renameSync } from "node:fs";
import { join } from "node:path";

export default function test(pi) {
  registerClaudeCli(pi);
  pi.on("session_start",async (_event,ctx) => {
    const results = {};
    const at = name => join(process.env.HOME,name);
    const tool = {name:"read",description:"Read through OMP",parameters:{type:"object",properties:{path:{type:"string"}},required:["path"],additionalProperties:false}};
    const model = {id:CLI_MODEL};
    const context = () => ({systemPrompt:["original system"],messages:[{role:"user",content:"request",timestamp:1}],tools:[tool]});
    const config = value => {
      for (const name of ["pid","capture.json","grandchild"]) if (existsSync(at(name))) unlinkSync(at(name));
      writeFileSync(at("case.json"),JSON.stringify(value));
    };
    const capture = () => JSON.parse(readFileSync(at("capture.json"),"utf8"));
    const sleep = ms => new Promise(resolve => setTimeout(resolve,ms));
    const run = async (value=context(),options,limits) => {
      const stream = streamClaudeCli(model,value,options,limits);
      const events = [];
      for await (const event of stream) events.push(event.type);
      return {message:await stream.result(),events};
    };
    const pidAt = name => Number(readFileSync(at(name),"utf8"));
    const isDead = pid => {try{process.kill(pid,0);return false;}catch(error){if(error.code==="ESRCH")return true;throw error;}};
    const dead = () => assert.equal(isDead(pidAt("pid")),true,"settled before direct child reaped");
    const failed = result => {
      assert.equal(result.message.stopReason,"error",JSON.stringify(result.message));
      assert.ok(result.message.errorMessage);
      assert.deepEqual(result.message.content,[]);
      assert.deepEqual(result.events,["start","error"],"invalid output leaked executable calls or partial success");
    };
    async function check(name,body) {
      try {config({});await body();results[name]={ok:true};}
      catch(error){results[name]={ok:false,error:error?.stack??String(error)};}
      finally {
        // Fixtures own intentional escaped daemons and clean them even on assertion failure.
        for (const name of ["grandchild","pid"]) if(existsSync(at(name))) {
          const pid=pidAt(name);
          if(!isDead(pid))try{process.kill(pid,"SIGKILL");}catch{}
        }
      }
    }
    await check("registration",async()=>{
      const registered=ctx.models.list().find(model=>model.provider===CLI_PROVIDER&&model.id===CLI_MODEL);
      assert.ok(registered);assert.equal(registered.api,CLI_PROVIDER);
    });
    await check("text_usage",async()=>{
      config({cost:0.125});const {message,events}=await run();
      assert.equal(message.stopReason,"stop");assert.equal(message.content[0].text,"answer");
      assert.deepEqual(events,["start","text_start","text_delta","text_end","done"]);
      assert.equal(message.usage.totalTokens,23);assert.equal(message.usage.input,11);
      assert.equal(message.usage.cacheRead,3);assert.equal(message.usage.cost.total,0.125);dead();
    });
    const proposed = (name="read",args='{"path":"a"}') => ({name,argumentsJson:args});
    await check("tools",async()=>{
      config({result:{text:"",toolCalls:[proposed(),proposed("read",'{"path":"b"}')]}});
      const {message,events}=await run();assert.equal(message.stopReason,"toolUse");
      assert.deepEqual(message.content.map(call=>call.arguments),[{path:"a"},{path:"b"}]);
      assert.notEqual(message.content[0].id,message.content[1].id);
      assert.deepEqual(events,["start","toolcall_start","toolcall_end","toolcall_start","toolcall_end","done"]);
    });
    await check("context_images_isolation",async()=>{
      const value=context();const big="unchanged-"+"x".repeat(1024*1024);
      value.messages=[
        {role:"developer",content:"developer instruction",timestamp:1},
        {role:"assistant",content:[{type:"thinking",thinking:"hidden",thinkingSignature:"signature"},{type:"redactedThinking",data:"hidden-redacted"},
          {type:"toolCall",id:"omp-call",name:"read",arguments:{path:"before"},thoughtSignature:"signature"}],credentialId:42,responseId:"secret-id",providerPayload:{secret:"opaque"}},
        {role:"toolResult",toolCallId:"omp-call",toolName:"read",isError:true,content:[{type:"text",text:"failed"},{type:"image",mimeType:"image/png",data:"aGVsbG8="}]},
        {role:"user",content:[{type:"text",text:big},{type:"image",mimeType:"image/jpeg",data:"aW1hZ2U="}],timestamp:2},
      ];
      const {message}=await run(value);assert.equal(message.stopReason,"stop",message.errorMessage);
      const got=capture(), wire=JSON.parse(got.input).message.content, payload=JSON.parse(wire[0].text);
      assert.deepEqual(payload.systemPrompt,["original system"]);
      assert.deepEqual(payload.messages.map(m=>m.role),["developer","assistant","toolResult","user"]);
      assert.equal(payload.messages[3].content[0].text,big);assert.equal(payload.messages[2].isError,true);
      assert.equal(payload.messages[2].toolCallId,"omp-call");
      assert.deepEqual(payload.messages[2].content[1],{type:"image",imageIndex:0});
      assert.deepEqual(payload.messages[3].content[1],{type:"image",imageIndex:1});
      assert.deepEqual(wire.slice(1).map(p=>p.source.media_type),["image/png","image/jpeg"]);
      assert.deepEqual(wire.slice(1).map(p=>p.source.data),["aGVsbG8=","aW1hZ2U="]);
      assert.deepEqual(payload.tools[0].parameters.required,["path"]);
      for(const secret of ["hidden","signature","secret-id","credentialId","opaque"])assert.equal(got.input.includes(secret),false);
      const argv=got.argv;
      for(const flag of ["--safe-mode","--restricted","--strict-mcp-config","--disable-slash-commands","--no-chrome","--no-session-persistence","--print"])assert.ok(argv.includes(flag),flag);
      for(const [flag,expected] of [["--tools",""],["--mcp-config",'{"mcpServers":{}}'],["--permission-prompts","none"],["--setting-sources",""],["--effort","high"],["--model",CLI_MODEL]])assert.equal(argv[argv.indexOf(flag)+1],expected);
      for(const flag of ["--bare","--dangerously-skip-permissions","--auto-approve","--resume","--continue","--settings"])assert.equal(argv.includes(flag),false);
      assert.equal(argv.join(" ").includes(big),false);
      assert.equal(got.env.ANTHROPIC_API_KEY,undefined);assert.equal(got.env.CLAUDE_CODE_SYSTEM_PROMPT,undefined);
    });
    for(const [name,configuration,value] of [
      ["unknown_tool",{result:{text:"answer",toolCalls:[proposed("bash","{}")]}}],
      ["invalid_args",{result:{text:"answer",toolCalls:[proposed("read",'{"path":2}')]}}],
      ["array_args",{result:{text:"",toolCalls:[proposed("read","[]")]}}],
      ["broken_args_json",{result:{text:"",toolCalls:[proposed("read","{")]}}],
      ["no_tools",{result:{text:"",toolCalls:[proposed()]}},{...context(),tools:[]}],
      ["empty",{result:{text:" ",toolCalls:[]}}],["bad_envelope",{envelope:{is_error:true}}],
      ["bad_subtype",{envelope:{subtype:"error_max_turns"}}],["missing_structured",{envelope:{structured_output:null,result:"prose"}}],
      ["invalid_json",{mode:"invalid"}],["nonzero_exit",{mode:"exit"}],
    ])await check(name,async()=>{config(configuration);failed(await run(value));dead();});
    await check("unsupported_image",async()=>{
      const value=context();value.messages[0].content=[{type:"image",mimeType:"image/tiff",data:"a"}];
      const result=await run(value);failed(result);assert.match(result.message.errorMessage,/image/);assert.equal(existsSync(at("pid")),false);
    });
    await check("preabort",async()=>{
      const controller=new AbortController();controller.abort();const {message}=await run(context(),{signal:controller.signal});
      assert.equal(message.stopReason,"aborted");assert.equal(existsSync(at("pid")),false);
    });
    await check("abort",async()=>{
      config({mode:"hang"});const controller=new AbortController();const pending=run(context(),{signal:controller.signal});
      const end=Date.now()+5000;while(!existsSync(at("capture.json"))&&Date.now()<end)await sleep(10);
      assert.ok(existsSync(at("capture.json")));controller.abort();const {message}=await pending;
      assert.equal(message.stopReason,"aborted");dead();
    });
    for(const mode of ["hang","overflow","stderr"])await check(mode,async()=>{
      config({mode});const result=await run(context(),undefined,{deadlineMs:mode==="hang"?500:5000,outputBytes:1024});
      failed(result);assert.match(result.message.errorMessage,mode==="hang"?/deadline/:/output limit/);dead();
    });
    await check("missing_executable",async()=>{
      const binary=at(".local/bin/claude");renameSync(binary,binary+".disabled");
      try{const result=await run();failed(result);assert.match(result.message.errorMessage,/not found/);}
      finally{renameSync(binary+".disabled",binary);}
    });
    await check("tool_choice_none",async()=>{
      config({result:{text:"",toolCalls:[proposed()]}});failed(await run(context(),{toolChoice:"none"}));
      const got=capture(),payload=JSON.parse(JSON.parse(got.input).message.content[0].text),schema=JSON.parse(got.argv[got.argv.indexOf("--json-schema")+1]);
      assert.equal(payload.toolChoice,"none");assert.deepEqual(payload.tools,[]);assert.equal(schema.properties.toolCalls.maxItems,0);
      config({});const result=await run(context(),{toolChoice:"none"});assert.equal(result.message.stopReason,"stop");
    });
    await check("tool_choice_named",async()=>{
      const value=context();value.tools.push({...tool,name:"write"});
      for(const choice of [{type:"function",name:"read"},{type:"function",function:{name:"read"}},{type:"tool",name:"read"}]){
        config({result:{text:"",toolCalls:[proposed("write")]}});failed(await run(value,{toolChoice:choice}));
        const got=capture(),payload=JSON.parse(JSON.parse(got.input).message.content[0].text),schema=JSON.parse(got.argv[got.argv.indexOf("--json-schema")+1]);
        assert.deepEqual(payload.toolChoice,choice);assert.deepEqual(payload.tools.map(t=>t.name),["read"]);
        assert.deepEqual(schema.properties.toolCalls.items.properties.name.enum,["read"]);assert.equal(schema.properties.toolCalls.minItems,1);
        config({});failed(await run(value,{toolChoice:choice}));
        config({result:{text:"",toolCalls:[proposed()]}});assert.equal((await run(value,{toolChoice:choice})).message.stopReason,"toolUse");
      }
    });
    await check("tool_choice_required",async()=>{
      for(const choice of ["required","any"]){
        config({});failed(await run(context(),{toolChoice:choice}));
        const got=capture(),schema=JSON.parse(got.argv[got.argv.indexOf("--json-schema")+1]);assert.equal(schema.properties.toolCalls.minItems,1);
        config({result:{text:"",toolCalls:[proposed()]}});assert.equal((await run(context(),{toolChoice:choice})).message.stopReason,"toolUse");
        config({});failed(await run({...context(),tools:[]},{toolChoice:choice}));assert.equal(existsSync(at("pid")),false);
      }
    });
    await check("tool_choice_invalid",async()=>{
      for(const choice of [{type:"tool",name:"unavailable"},{type:"computer"}]){
        config({});failed(await run(context(),{toolChoice:choice}));assert.equal(existsSync(at("pid")),false);
      }
    });
    await check("forced_then_none",async()=>{
      config({result:{text:"",toolCalls:[proposed()]}});assert.equal((await run(context(),{toolChoice:{type:"tool",name:"read"}})).message.stopReason,"toolUse");
      config({result:{text:"",toolCalls:[proposed()]}});failed(await run(context(),{toolChoice:"none"}));
    });
    for(const [name,mode,abort] of [["group_abort","group",true],["group_deadline","group",false],["escaped_pipe_deadline","escaped",false]])await check(name,async()=>{
      config({mode});const controller=new AbortController();const start=Date.now();
      const pending=run(context(),{signal:controller.signal},{deadlineMs:abort?5000:1000});
      const end=Date.now()+5000;while(!existsSync(at("grandchild"))&&Date.now()<end)await sleep(10);
      assert.ok(existsSync(at("grandchild")),"grandchild never started");
      if(abort)controller.abort();const result=await pending;
      assert.ok(Date.now()-start<4000,"descendant-held pipe defeated finite deadline");
      assert.equal(result.message.stopReason,abort?"aborted":"error");dead();
      if(mode==="group"){
        const end=Date.now()+2000;while(!isDead(pidAt("grandchild"))&&Date.now()<end)await sleep(10);
        assert.equal(isDead(pidAt("grandchild")),true,"normal descendant survived group kill");
      }else assert.equal(isDead(pidAt("grandchild")),false,"escaped fixture not exercising open-pipe case");
    });
    writeFileSync(process.env.CLI_TEST_REPORT,JSON.stringify(results));ctx.shutdown();
  });
}
'''


class CliInferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        omp = os.environ.get("OMP_CLI_TEST_OMP") or shutil.which("omp")
        if not omp:
            candidate = Path.home() / ".local/bin/omp"
            omp = str(candidate) if candidate.is_file() else None
        if not omp:
            raise unittest.SkipTest("requires native OMP 18.14.0")
        cls.temporary = tempfile.TemporaryDirectory(prefix="dev-stack-cli-offline-")
        cls.addClassCleanup(cls.temporary.cleanup)
        root = Path(cls.temporary.name).resolve()
        home, project = root / "home", root / "project"
        agent, binary = home / ".omp/agent", home / ".local/bin/claude"
        agent.mkdir(parents=True)
        binary.parent.mkdir(parents=True)
        project.mkdir()
        (agent / "mcp.json").write_text('{"mcpServers":{}}\n')
        (agent / "config.yml").write_text("modelRoles: {}\n")
        binary.write_text("#!" + sys.executable + "\n" + FAKE)
        binary.chmod(0o700)
        adapter = ROOT / "integrations/omp-ui-ux/claude-cli.ts"
        harness, report = root / "harness.ts", root / "report.json"
        harness.write_text("import { streamClaudeCli, registerClaudeCli, CLI_MODEL, CLI_PROVIDER } from " +
                           json.dumps(os.path.relpath(adapter, root)) + ";\n" + HARNESS)
        env = {key: os.environ[key] for key in ("TMPDIR", "LANG", "LC_ALL") if key in os.environ}
        env.update(HOME=str(home), PATH="/usr/bin:/bin:/usr/sbin:/sbin",
                   XDG_CONFIG_HOME=str(home / ".config"), XDG_CACHE_HOME=str(home / ".cache"),
                   XDG_DATA_HOME=str(home / ".local/share"), PI_CODING_AGENT_DIR=str(agent), OMP_AGENT_DIR=str(agent),
                   ANTHROPIC_API_KEY="offline-catalog-placeholder", CLAUDE_CODE_SYSTEM_PROMPT="must-not-propagate", CLI_TEST_REPORT=str(report))
        stdout, stderr = root / "stdout.log", root / "stderr.log"
        with stdout.open("w") as out, stderr.open("w") as err:
            process = subprocess.Popen([omp,"--mode","rpc","--no-session","--no-skills","--no-rules",
                                        "--no-lsp","--trusted-extension",str(harness)],cwd=project,env=env,
                                       stdin=subprocess.PIPE,stdout=out,stderr=err,text=True)
            try:
                deadline = time.monotonic() + 120
                while not report.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.05)
                if not report.exists():
                    raise AssertionError("CLI harness produced no report.\n" + stdout.read_text()[-12000:] + stderr.read_text()[-12000:])
                cls.results = json.loads(report.read_text())
            finally:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                # Final safety net if the native harness failed before fixture cleanup.
                for name in ("grandchild","pid"):
                    path = home / name
                    if path.exists():
                        try:
                            os.kill(int(path.read_text()),signal.SIGKILL)
                        except ProcessLookupError:
                            pass

    def test_offline_process_cases(self):
        expected = {"registration","text_usage","tools","context_images_isolation","unknown_tool","invalid_args",
                    "array_args","broken_args_json","no_tools","empty","bad_envelope","bad_subtype","missing_structured",
                    "invalid_json","nonzero_exit","unsupported_image","preabort","abort","hang","overflow","stderr",
                    "missing_executable","tool_choice_none","tool_choice_named","tool_choice_required","tool_choice_invalid",
                    "forced_then_none","group_abort","group_deadline","escaped_pipe_deadline"}
        self.assertEqual(set(self.results),expected)
        for name in sorted(expected):
            with self.subTest(case=name):
                self.assertTrue(self.results[name]["ok"],self.results[name].get("error"))


if __name__ == "__main__":
    unittest.main()
