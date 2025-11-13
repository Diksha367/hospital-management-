# app/hospital_core.py
from datetime import datetime
import itertools

class Patient:
    _ids = itertools.count(1)
    def __init__(self, name: str, disease: str, priority: int):
        self.id = next(Patient._ids)
        self.name = name.strip()
        self.disease = disease.strip()
        self.priority = int(priority)
        self.admit_time = datetime.now()

    def to_row(self):
        return {
            "id": self.id,
            "name": self.name,
            "disease": self.disease,
            "priority": self.priority,
            "admit_time": self.admit_time.strftime("%Y-%m-%d %H:%M:%S")
        }

class PatientNode:
    def __init__(self, patient: Patient):
        self.patient = patient
        self.next = None

class PatientLinkedList:
    def __init__(self):
        self.head = None

    def add(self, patient: Patient):
        node = PatientNode(patient)
        if self.head is None or patient.priority < self.head.patient.priority:
            node.next = self.head
            self.head = node
            return
        prev = None
        cur = self.head
        while cur and cur.patient.priority <= patient.priority:
            prev = cur
            cur = cur.next
        prev.next = node
        node.next = cur

    def remove_by_id(self, patient_id: int):
        prev = None
        cur = self.head
        while cur:
            if cur.patient.id == patient_id:
                if prev:
                    prev.next = cur.next
                else:
                    self.head = cur.next
                cur.next = None
                return cur.patient
            prev = cur
            cur = cur.next
        return None

    def to_list(self):
        out = []
        cur = self.head
        while cur:
            out.append(cur.patient)
            cur = cur.next
        return out

    def clear(self):
        self.head = None

class DischargeStack:
    def __init__(self):
        self._stack = []

    def push(self, patient: Patient, reason: str = ""):
        self._stack.append((patient, datetime.now(), reason))

    def pop(self):
        if not self._stack:
            return None
        return self._stack.pop()

    def to_list(self):
        return list(self._stack)

    def clear(self):
        self._stack.clear()

class HospitalSystem:
    def __init__(self):
        self.active = PatientLinkedList()
        self.discharged = DischargeStack()
        self.history = []

    def add_patient(self, name: str, disease: str, priority: int):
        if not name.strip() or not disease.strip():
            raise ValueError("Name and disease cannot be empty")
        if int(priority) < 1:
            raise ValueError("Priority must be >= 1")
        p = Patient(name, disease, int(priority))
        self.active.add(p)
        return p

    def discharge_patient(self, patient_id: int, reason: str = ""):
        p = self.active.remove_by_id(patient_id)
        if not p:
            raise LookupError(f"Patient with id {patient_id} not found")
        self.discharged.push(p, reason)
        self.history.append({"patient": p, "time": datetime.now(), "reason": reason})
        return p

    def undo_last_discharge(self):
        item = self.discharged.pop()
        if not item:
            raise LookupError("No discharge to undo")
        patient, _, _ = item
        self.active.add(patient)
        # remove last matching history record
        for i in range(len(self.history)-1, -1, -1):
            if self.history[i]["patient"].id == patient.id:
                self.history.pop(i)
                break
        return patient

    def view_active(self):
        return self.active.to_list()

    def view_discharged(self):
        # top-first
        return list(reversed(self.discharged.to_list()))

    def view_history(self):
        return self.history

    def reset(self):
        self.active.clear()
        self.discharged.clear()
        self.history.clear()
