import * as THREE from 'three';
import { useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { MeshTransmissionMaterial, Text, Environment } from '@react-three/drei';
import { easing } from 'maath';

function Lens({ modeProps }) {
  const ref = useRef();
  const { viewport } = useThree();

  useFrame((state, delta) => {
    const { pointer } = state;
    const destX = (pointer.x * viewport.width) / 2;
    const destY = (pointer.y * viewport.height) / 2;
    easing.damp3(ref.current.position, [destX, destY, 2], 0.15, delta);
  });

  return (
    <mesh ref={ref} scale={2.5} rotation-x={Math.PI / 2}>
      <cylinderGeometry args={[1, 1, 0.3, 64]} />
      <MeshTransmissionMaterial
        ior={1.05}
        thickness={3}
        chromaticAberration={0.03}
        anisotropy={0.01}
        transmission={1}
        roughness={0}
        clearcoat={1}
        {...modeProps}
      />
    </mesh>
  );
}
