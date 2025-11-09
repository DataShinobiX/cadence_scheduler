import { Fragment, useEffect, useMemo, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';

export default function MealOrderModal({
  isOpen,
  onClose,
  initialMessage,
  meal = 'lunch',
  onPlaced, // optional callback when order completes
}) {
  const [step, setStep] = useState('ask'); // ask | searching | options | ordering | done
  const [selectedOption, setSelectedOption] = useState(null);

  useEffect(() => {
    if (!isOpen) {
      // reset when closed
      setStep('ask');
      setSelectedOption(null);
    }
  }, [isOpen]);

  const mockOptions = useMemo(() => {
    const common = [
      { id: 'thai_green', name: 'Green Curry Bowl', vendor: 'Thai Express', eta: '25–35m', price: '$12.50' },
      { id: 'med_bowl', name: 'Falafel & Hummus Bowl', vendor: 'Mediterranean Grill', eta: '20–30m', price: '$11.00' },
      { id: 'poke', name: 'Salmon Poke Bowl', vendor: 'Aloha Poke', eta: '30–40m', price: '$14.75' },
    ];
    const dinnerExtras = [
      { id: 'pizza', name: 'Margherita Pizza', vendor: 'Napoli Pizza', eta: '35–45m', price: '$15.00' },
      { id: 'indian', name: 'Paneer Tikka Masala', vendor: 'Spice Route', eta: '30–40m', price: '$13.50' },
    ];
    return meal === 'dinner' ? [...common, ...dinnerExtras] : common;
  }, [meal]);

  const handleYes = () => {
    setStep('searching');
    setTimeout(() => setStep('options'), 5000);
  };

  const handleNo = () => {
    onClose && onClose();
  };

  const handleSelect = (option) => {
    setSelectedOption(option);
    setStep('ordering');
    setTimeout(() => {
      setStep('done');
      onPlaced && onPlaced(option);
    }, 5000);
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300" enterFrom="opacity-0" enterTo="opacity-100"
          leave="ease-in duration-200" leaveFrom="opacity-100" leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300" enterFrom="opacity-0 scale-95" enterTo="opacity-100 scale-100"
              leave="ease-in duration-200" leaveFrom="opacity-100 scale-100" leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                {/* Header */}
                <Dialog.Title className="text-lg font-semibold text-gray-900">
                  {step === 'ask' && 'Order ' + meal + '?'}
                  {step === 'searching' && 'Looking for options'}
                  {step === 'options' && 'Choose an option'}
                  {step === 'ordering' && 'Placing your order'}
                  {step === 'done' && 'Order placed'}
                </Dialog.Title>

                {/* Content */}
                <div className="mt-3">
                  {step === 'ask' && (
                    <>
                      <p className="text-sm text-gray-600 mb-4">{initialMessage || `Should I order ${meal} for you from takeaway.com?`}</p>
                      <div className="flex gap-3">
                        <button
                          className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                          onClick={handleYes}
                        >
                          Yes
                        </button>
                        <button
                          className="inline-flex items-center justify-center rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-800 hover:bg-gray-200"
                          onClick={handleNo}
                        >
                          No
                        </button>
                      </div>
                    </>
                  )}

                  {step === 'searching' && (
                    <div className="flex items-center gap-3 text-gray-700">
                      <svg className="h-5 w-5 animate-spin text-blue-600" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                      </svg>
                      <span>Looking for options that match your preferences…</span>
                    </div>
                  )}

                  {step === 'options' && (
                    <div className="space-y-3">
                      {mockOptions.map((opt) => (
                        <button
                          key={opt.id}
                          className="w-full text-left border border-gray-200 hover:border-blue-300 rounded-lg p-3 transition-colors"
                          onClick={() => handleSelect(opt)}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium text-gray-900">{opt.name}</p>
                              <p className="text-sm text-gray-600">{opt.vendor} • {opt.eta}</p>
                            </div>
                            <span className="text-gray-900 font-semibold">{opt.price}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {step === 'ordering' && (
                    <div className="flex items-center gap-3 text-gray-700">
                      <svg className="h-5 w-5 animate-spin text-blue-600" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                      </svg>
                      <span>Placing your order for “{selectedOption?.name}”…</span>
                    </div>
                  )}

                  {step === 'done' && (
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0">
                        <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                      </div>
                      <div>
                        <p className="text-gray-900 font-medium">Order placed!</p>
                        <p className="text-sm text-gray-600">
                          “{selectedOption?.name}” from {selectedOption?.vendor}. ETA {selectedOption?.eta}.
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="mt-6 flex justify-end">
                  <button
                    className="inline-flex items-center justify-center rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-800 hover:bg-gray-200"
                    onClick={onClose}
                  >
                    {step === 'done' ? 'Close' : 'Cancel'}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}


