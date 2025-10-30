# test_lobster.py
import rrndbd

def main():
    print("Testing rrndbd import...")
    print(f"rrndbd module location: {rrndbd.__file__}")

    # Check if we can access the LobsterPlot class
    try:
        plot = rrndbd.lobster.LobsterPlot()
        print("✅ Successfully created LobsterPlot instance.")
    except Exception as e:
        print("❌ Failed to create LobsterPlot instance:")
        print(e)
        return

    # Optional: check inheritance
    from rrndbd.base import BasePlot
    assert isinstance(plot, BasePlot), "LobsterPlot should inherit from BasePlot"
    print("✅ Inheritance check passed.")

    print("All tests passed!")

    plot.show()
if __name__ == "__main__":
    main()
