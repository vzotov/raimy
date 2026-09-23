interface EquipmentListProps {
  equipment: string[];
}

export default function EquipmentList({ equipment }: EquipmentListProps) {
  if (equipment.length === 0) return null;

  return (
    <ul className="flex flex-wrap gap-2">
      {equipment.map((item) => (
        <li
          key={item}
          className="px-3 py-1.5 bg-accent/10 text-text/80 text-sm rounded-full"
        >
          {item}
        </li>
      ))}
    </ul>
  );
}
