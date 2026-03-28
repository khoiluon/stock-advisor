import { StarIcon } from "@phosphor-icons/react/dist/csr/Star";
import { TrashIcon } from "@phosphor-icons/react/dist/csr/Trash";
import { Button } from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import useFavoritesQuery from "@/services/useFavoritesQuery";
import useToggleFavoriteMutate from "@/services/useToggleFavoriteMutate";
import type { UserFavorite } from "@/types/Stock";

export default function Favorites() {
	const { data: favorites } = useFavoritesQuery();

	const { mutate: toggleFavorite } = useToggleFavoriteMutate();

	const handleDelete = (favorite: UserFavorite) => {
		toggleFavorite({ stockTicker: favorite.stock.ticker, favorited: favorite });
	};

	return (
		<main className="mt-12">
			<Card className="w-full max-w-3xl mx-auto">
				<div className="flex justify-between items-center mb-8">
					<h1 className="text-3xl font-bold text-white">Favorite Stocks</h1>
				</div>

				<div className="text-right text-gray-400 text-xs mb-4">
					{favorites?.length} stock{favorites?.length !== 1 ? "s" : ""} in
					favorites
				</div>
				<div className="flex flex-col gap-4">
					{favorites?.map((fav) => (
						<Card
							key={fav.id}
							className="flex items-center justify-between bg-slate-900"
						>
							<div className="flex items-center gap-4">
								<StarIcon size={24} weight="fill" className="text-yellow-400" />
								<div>
									<div className="text-xl font-bold text-white">
										{fav.stock.ticker}
									</div>
									<div className="text-gray-300 text-sm">
										{fav.stock.company_name}
									</div>
									<div className="text-gray-400 text-xs mt-1">
										Added on:{" "}
										{new Date(fav.added_at).toLocaleDateString("en-US")}
									</div>
								</div>
							</div>
							<div className="flex items-center space-x-2">
								<Button
									size="icon"
									variant="destructive"
									onClick={() => handleDelete(fav)}
								>
									<TrashIcon size={20} />
								</Button>
							</div>
						</Card>
					))}
				</div>
			</Card>
		</main>
	);
}
