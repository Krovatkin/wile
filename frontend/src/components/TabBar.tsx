// Tab bar component for managing multiple tabs


interface TabBarProps {
  tabs: Array<{ id: string; label: string }>;
  activeTabId: string;
  onTabClick: (tabId: string) => void;
  onTabClose: (tabId: string) => void;
  onAddTab: () => void;
}

export function TabBar({ tabs, activeTabId, onTabClick, onTabClose, onAddTab }: TabBarProps) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <div id="tabsContainer" className="flex gap-1 flex-wrap">
        {tabs.map((tab) => (
          <div key={tab.id} id={`tab-header-${tab.id}`} className="flex items-center gap-1">
            <button
              className={`btn btn-sm rounded-md ${
                activeTabId === tab.id
                  ? 'btn-active bg-blue-500 text-white'
                  : 'btn-outline'
              }`}
              onClick={() => onTabClick(tab.id)}
            >
              {tab.label}
            </button>
            {tabs.length > 1 && (
              <button
                className="btn btn-xs btn-ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  onTabClose(tab.id);
                }}
              >
                ✕
              </button>
            )}
          </div>
        ))}
      </div>
      <button
        id="addTabBtn"
        className="btn btn-sm rounded-md bg-blue-400 hover:bg-blue-500 text-white border-blue-400"
        onClick={onAddTab}
      >
        +
      </button>
    </div>
  );
}
