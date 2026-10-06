"""Resumable paid regeneration from a separated-hands reference; originals preserved."""
from pathlib import Path
import meshy_baedoli_ultra as job

ROOT = Path(__file__).resolve().parents[1]
job.OUT = ROOT / 'outputs/baedoli-meshy71-clean-20261002'
job.ASSETS = ROOT / 'assets/npc/meshy71-baedoli-clean-20261002'
job.STATE = job.OUT / 'task-state.json'
job.REFERENCE = job.ASSETS / 'reference-a-pose.png'
# The reference already specifies the mascot anatomy; human pose conversion is avoided.
job.SETTINGS = {**job.SETTINGS, 'pose_mode': ''}

if __name__ == '__main__':
    job.main()
