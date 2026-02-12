"use client";
import { Button } from '@/components/ui/button';
export function RegistrationButton({ registered, onRegister, onCancel }: { registered: boolean; onRegister: () => void; onCancel: () => void }) { return registered ? <Button variant="danger" onClick={onCancel}>Cancel Registration</Button> : <Button onClick={onRegister}>Register</Button>; }
