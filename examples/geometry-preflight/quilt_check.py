"""Original scalar fixture, not a Blender render or cloth simulation. Python stdlib."""
import json
import math


def height_uv(u, v, base=0.18, amplitude=0.012):
    return base + amplitude * math.sin(math.pi * u)**2 * math.sin(math.pi * v)**2


def height_xy(x, y, pitch=0.3):
    if not math.isfinite(pitch) or pitch <= 0:
        raise ValueError('pitch must be finite and positive')
    return height_uv((x+y)/(math.sqrt(2)*pitch), (x-y)/(math.sqrt(2)*pitch))


def spread(values):
    return max(values)-min(values)


def run():
    # Synthetic 11 x 16 quad grid reproduces the reported scalar counts only.
    nx, ny, H, depth = 11, 16, 0.2, 0.02
    old = {(i,j): H-depth if 0<i<nx and 0<j<ny else H
           for i in range(nx+1) for j in range(ny+1)}
    interior = [old[i,j] for i in range(1,nx) for j in range(1,ny)]
    flat = sum(spread([old[i,j],old[i+1,j],old[i,j+1],old[i+1,j+1]])<1e-12
               for i in range(nx) for j in range(ny))
    assert len(interior)==150 and flat==126 and spread(interior)==0
    # Negative control: nonzero variation alone admits an ordinary sloped plane.
    slope = [0.18+0.01*i/nx for i in range(1,nx) for j in range(1,ny)]
    assert spread(slope)>0
    assert abs(height_uv(0,0.5)-0.18)<1e-12
    assert abs(height_uv(0.5,0.5)-0.192)<1e-12
    assert abs(height_uv(0.37,0.61)-height_uv(1.37,0.61))<1e-12
    assert abs(height_uv(0.37,0.61)-height_uv(0.37,1.61))<1e-12
    # Negative control: samples exactly on the seams miss all the raised centres.
    aliased=[height_uv(i,j) for i in range(5) for j in range(5)]
    dense=[height_uv(i/8,j/8) for i in range(33) for j in range(33)]
    assert spread(aliased)<1e-12 and abs(spread(dense)-0.012)<1e-12
    pitch=0.3
    assert abs(height_xy(pitch/math.sqrt(2),0)-0.192)<1e-12
    return {'baseline':{'interior_vertices':len(interior),'flat_quads':flat,'total_quads':nx*ny,'interior_height_range':spread(interior)},
            'negative_controls':{'slope_passes_variation_check':True,'seam_only_samples_height_range':spread(aliased)},
            'proposed_field':{'base':0.18,'amplitude':0.012,'sampled_height_range':spread(dense),'seam_and_peak_checks':True,'periodicity_both_axes':True,'rotation_mapping':True},
            'scope':'Scalar arithmetic only. No Blender, mesh topology, normals, render, cloth simulation, reference comparison or agent-quality benchmark.'}


if __name__=='__main__':
    print(json.dumps(run(),indent=2))
