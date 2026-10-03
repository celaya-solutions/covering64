# Document:    Independent Heavy-Profile Predicate and Rollback Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      ba32bf0ece7c37acf628f7a99f6ab9f2fa1bd21baa4d6bb5952a46cfc77da9fd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
SCRATCH = pathlib.Path('experiments/scratch/heavy-profile-predicate-audit-20261003')
HARNESS = r'''
bool oracle(const State& state) {
  std::vector<int> ids;
  for (int t=0;t<560;++t) if (state.count[t]>=6) ids.push_back(t);
  int n=int(ids.size());
  for(int a=0;a<n;++a) for(int b=a+1;b<n;++b) for(int c=b+1;c<n;++c)
  for(int d=c+1;d<n;++d) for(int e=d+1;e<n;++e) {
    std::array<int,16> hits{}; int seven=0;
    for(int j : {a,b,c,d,e}) {
      int id=ids[j]; seven+=state.count[id]>=7;
      for(int p=0;p<16;++p) if (triples[id]&(1u<<p)) ++hits[p];
    }
    if(seven>=2 && *std::max_element(hits.begin(),hits.end())<=1) return true;
  }
  return false;
}
void independent_recount(const State& state,const std::vector<int>& heavy) {
  std::array<int,560> count{};
  std::array<bool,4368> selected{};
  for(int id : state.ids) {
    if(selected[id]) throw std::runtime_error("duplicate selected block");
    selected[id]=true;
    for(int t=0;t<560;++t)
      if((triples[t]&blocks[id].mask)==triples[t]) ++count[t];
  }
  int deficit=0;std::vector<int> expected;
  for(int t=0;t<560;++t) {deficit+=count[t]==0;if(count[t]>=6)expected.push_back(t);}
  auto actual=heavy;std::sort(actual.begin(),actual.end());
  if(count!=state.count||selected!=state.selected||deficit!=state.deficit||actual!=expected)
    throw std::runtime_error("independent recount mismatch");
}
int main(int argc,char**argv) {
  if(argc!=2)return 2;
  universe();std::mt19937_64 audit_rng(2026100387);
  unsigned checked=0,positive=0;
  for(int trial=0;trial<4000;++trial) {
    State state({});
    if(trial<2000) {
      std::array<int,16> points{};std::iota(points.begin(),points.end(),0);
      std::shuffle(points.begin(),points.end(),audit_rng);
      for(int i=0;i<5;++i) {
        unsigned mask=(1u<<points[3*i])|(1u<<points[3*i+1])|(1u<<points[3*i+2]);
        auto at=std::find(triples.begin(),triples.end(),mask);
        state.count[at-triples.begin()]=6+int(audit_rng()%3);
      }
    }
    int extra=int(audit_rng()%9);
    for(int i=0;i<extra;++i) state.count[audit_rng()%560]=6+int(audit_rng()%4);
    auto heavy=heavy_ids(state);std::shuffle(heavy.begin(),heavy.end(),audit_rng);
    bool expected=oracle(state),actual=forbidden_profile(heavy,state);
    if(actual!=expected)throw std::runtime_error("predicate mismatch");
    ++checked;positive+=expected;
  }
  State state(read_blocks(argv[1]));auto heavy=heavy_ids(state);
  unsigned moves=0,rollbacks=0;
  for(int trial=0;trial<5000;++trial) {
    int slot=int(audit_rng()%64),old=state.ids[slot],next=int(audit_rng()%4368);
    if(state.selected[next])continue;
    state.move(slot,next);update_heavy(heavy,state,old,next);
    independent_recount(state,heavy);++moves;
    if(audit_rng()%2) {
      state.move(slot,old);update_heavy(heavy,state,old,next);
      independent_recount(state,heavy);++rollbacks;
    }
  }
  std::cout<<"{\"synthetic_profiles\":"<<checked<<",\"positive_profiles\":"<<positive
    <<",\"moves\":"<<moves<<",\"rollbacks\":"<<rollbacks<<"}\n";
}
'''


def main():
    source = pathlib.Path('scripts/heavy_profile_heuristic.cpp')
    raw = source.read_text()
    prefix = raw.split('int main(int argc, char** argv)', 1)[0]
    assert len(prefix) < len(raw)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    harness = SCRATCH / 'harness.cpp'
    harness.write_text('#include <numeric>\n' + prefix + HARNESS)
    executable = SCRATCH / 'check'
    compile_command = ['c++', '-std=c++17', '-O1', '-g', '-fsanitize=address,undefined',
                       '-Wall', '-Wextra', '-pedantic', '-I', 'scripts', str(harness),
                       '-o', str(executable)]
    process = subprocess.run(compile_command, capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    candidate = pathlib.Path('experiments/2026-10-03/heuristic-tabu-2026100301-deficit-3.txt')
    run = subprocess.run([str(executable), str(candidate)], capture_output=True, text=True)
    assert run.returncode == 0 and not run.stderr, run.stderr
    result = dict(complete=True, seed=2026100387, result=json.loads(run.stdout),
                  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  dependency_sha256=hashlib.sha256(pathlib.Path('scripts/heuristic_search.cpp')
                                                   .read_bytes()).hexdigest(),
                  harness_sha256=hashlib.sha256(harness.read_bytes()).hexdigest(),
                  auditor_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                  compile_command=compile_command, compiler=subprocess.check_output(
                      ['c++', '--version'], text=True).splitlines()[0],
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                          text=True).strip(),
                  sanitizer_diagnostics=run.stderr)
    (ROOT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['result']))


if __name__ == '__main__':
    main()
