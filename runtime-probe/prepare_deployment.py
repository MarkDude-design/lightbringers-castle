"""Generate reviewable SDK arguments only. Never deploys or reads credentials."""
import argparse
import json
from pathlib import Path
import re
import uuid


def prepare(repo, sha, name='historical-runtime-probe', build_directory='.'):
    if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):
        raise ValueError('Use a GitHub HTTPS repository URL with no credentials, query or fragment')
    if not re.fullmatch(r'[0-9a-fA-F]{40}',sha):
        raise ValueError('A full immutable 40-character commit SHA is required; branch/tag names are rejected')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',name):raise ValueError('Invalid deployment name')
    if build_directory.startswith('/') or '..' in build_directory.split('/') or '\\' in build_directory:
        raise ValueError('build_directory must be a relative directory inside the repository')
    deployment={'name':name,'spec':{'github_url':repo,'revision':sha.lower(),
                'backend_spec':{'type':'koyeb','build_directory':build_directory,'dockerfile_path':'Dockerfile'}}}
    execution={'workflow_identifier':'historical-runtime-probe-v1','deployment_name':name,
               'input':{'probe_id':'probe-'+uuid.uuid4().hex}}
    return deployment,execution


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',required=True);parser.add_argument('--sha',required=True)
    parser.add_argument('--name',default='historical-runtime-probe')
    parser.add_argument('--build-directory',default='.')
    parser.add_argument('--output-directory',type=Path,default=Path('.'))
    args=parser.parse_args()
    deployment,execution=prepare(args.repo,args.sha,args.name,args.build_directory)
    args.output_directory.mkdir(parents=True,exist_ok=True)
    for filename,data in [('deployment.args.json',deployment),('execution.args.json',execution)]:
        (args.output_directory/filename).write_text(json.dumps(data,indent=2)+'\n')
    print('Wrote deployment.args.json and execution.args.json; no deployment performed.')
